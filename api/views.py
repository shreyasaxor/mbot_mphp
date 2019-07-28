from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import pandas as pd
import math
from collections import Counter
import csv
import json
from rake_nltk import Rake
import numpy as np
import sklearn.metrics as m
from sklearn.preprocessing import LabelEncoder
import random
from sklearn.ensemble import RandomForestClassifier


# Create your views here.

from .vector import text_to_vector,get_cosine

noise_list = ["is", "a", "this", "...", "+", "-", "and", "with", "Create", "Generate", "test"] 

def _remove_noise(input_text):
    words = input_text.split() 
    noise_free_words = [word for word in words if word not in noise_list] 
    noise_free_text = " ".join(noise_free_words) 
    return noise_free_text


def get_cosine(vec1, vec2):
    common = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in common])

    sum1 = sum([vec1[x]**2 for x in vec1.keys()]) 
    sum2 = sum([vec2[x]**2 for x in vec2.keys()]) 
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
   
    if not denominator:
        return 0.0 
    else:
        return float(numerator) / denominator

def text_to_vector(text): 
    words = text.split() 
    return Counter(words)    

@api_view(['Post'])
def recommend_config(request):
    search_query = request.data.get('query',None)
    if not search_query:
        return Response("Invalid search query",status=400)

    corpus = pd.read_excel('data/master_configs.xlsx')
    print('reached...')
    # initializing the new column
    corpus['Key_words'] = ""

    for index, row in corpus.iterrows():
        info = row['Info']
        
        # instantiating Rake, by default it uses english stopwords from NLTK
        # and discards all puntuation characters as well
        r = Rake()

        # extracting the words by passing the text
        r.extract_keywords_from_text(info)

        # getting the dictionary whith key words as keys and their scores as values
        key_words_dict_scores = r.get_word_degrees()
        
        # assigning the key words to the new column for the corresponding movie
        row['Key_words'] = list(key_words_dict_scores.keys())

    # dropping the Plot column
    corpus.drop(columns = ['Info'], inplace = True)

    corpus.set_index('Name', inplace = True)

    corpus['bag_of_words'] = ''
    columns = corpus.columns
    for index, row in corpus.iterrows():
        words = ''
        for col in columns:
            if col != 'Key_words':
                words = words + row[col]+ ' '
            else:
                words = words + ' '.join(row[col])+ ' '
        row['bag_of_words'] = words  

    corpus['config_id'] = ''
    columns = corpus.columns
    for index, row in corpus.iterrows():
        words = ''
        for col in columns:
            if col == 'OS' or col == 'Server' or col == 'Controller':
                words = words + row[col]+ '|'
        row['config_id'] = words

    search_query = _remove_noise(search_query)
    vector1 = text_to_vector( search_query.lower() )

    result = {'Rank':[], 'Heading':[], 'Config':[], 'Cosine':[]}


    for i in corpus.index :
        config = corpus['bag_of_words'][i]
        config = _remove_noise(config)
        
        vector2 = text_to_vector( config.lower() )
        
        cosine = get_cosine ( vector1, vector2 )
        if cosine > 0 :
            result['Rank'].append(0)
            result['Heading'].append(i)
            result['Config'].append(corpus['config_id'][i])
            result['Cosine'].append(cosine)

    result_df = pd.DataFrame(data=result)

    result_df = result_df.sort_values( 'Cosine', ascending=False )


    result_df.to_csv('data/config_op.csv')
    #print(result_df)
    print('Output saved!')     

    #convert csv to json
    csvfilename = 'data/config_op.csv'
    jsonfilename = csvfilename.split('.')[0] + '.json'
    csvfile = open(csvfilename, 'r')
    jsonfile = open(jsonfilename, 'w')
    reader = csv.DictReader(csvfile)

    fieldnames = ('Rank', 'Heading', 'Config', 'Cosine')

    output = []

    for each in reader:
        row = {}
        for field in fieldnames:
            row[field] = each[field]
        output.append(row)

    json.dump(output, jsonfile, indent=2, sort_keys=True)




    #print(result_df)
    print('Output saved!')
    return Response(output)

@api_view(['Post'])
def recommend_test(request):

    search_query = request.data.get('query',None)
    if not search_query:
        return Response("Invalid search query",status=400)

    corpus = pd.read_excel('data/input_testcases.xlsx')

    result = { 'TestCase':[], 'Cosine':[], 'Effort':[]}



    search_query = _remove_noise(search_query)
    vector1 = text_to_vector( search_query.lower() )

    for i in corpus.index :
        test_case = corpus['Test case'][i] + ' ' + corpus['Type'][i]
        test_case = _remove_noise(test_case)
        
        vector2 = text_to_vector( test_case.lower() )
        
        cosine = get_cosine ( vector1, vector2 )
        if cosine > 0 :
            result['TestCase'].append(corpus['Test case'][i])
            result['Cosine'].append(cosine)
            result['Effort'].append(corpus['Effort'][i])


    result_df = pd.DataFrame(data=result)
    print(result_df)

    result_df = result_df.sort_values( 'Cosine', ascending=False )
    result_df.to_csv('data/similarity_output.csv',columns=['TestCase','Cosine','Effort'],index=False)

    #------------------------

    df1 = pd.read_csv('data/history.csv')
    df2 = pd.read_csv('data/similarity_output.csv')

    #include common test cases
    include_common = request.data.get('include_common',None)
    if include_common == "true" :
        df3 = pd.read_csv('data/common_testcases.csv')
        new_df = pd.concat([df2, df3])
        merged_df = pd.merge(df1, new_df, on=['TestCase'], how='inner')
    elif include_common == "false" :
        merged_df = pd.merge(df1, df2, on=['TestCase'], how='inner')
    else :
        return Response("Invalid value for include_common",status=400)

    merged_df = merged_df.sort_values( 'Cosine', ascending=False )

    merged_df.to_csv('data/prediction_input.csv')



    train = pd.read_csv('data/history.csv')
    test = pd.read_csv('data/prediction_input.csv')
    train['_Type']='Train' #Create a flag for Train and Test Data set
    test['_Type']='Test'
    fullData = pd.concat([train,test],axis=0) #Combined both Train and Test Data set

    ID_col = ['']
    target_col = ["TEST_STATUS"]
    cat_cols = ['TEST_ID','TYPE','PROJECT','EXEC_TYPE']
    num_cols = ['ID']
    other_col=['_Type'] #Test and Train Data set identifier
    omit_col = ['']

    num_cat_cols = num_cols+cat_cols # Combined numerical and Categorical variables

    #Create a new variable for each variable having missing value with VariableName_NA 
    # and flag missing value with 1 and other with 0

    for var in num_cat_cols:
        if fullData[var].isnull().any()==True:
            fullData[var+'_NA']=fullData[var].isnull()*1 

    #Impute numerical missing values with mean
    fullData[num_cols] = fullData[num_cols].fillna(fullData[num_cols].mean(),inplace=True)

    #Impute categorical missing values with -9999
    fullData[cat_cols] = fullData[cat_cols].fillna(value = -9999)

    #create label encoders for categorical features
    for var in cat_cols:
        number = LabelEncoder()
        fullData[var] = number.fit_transform(fullData[var].astype('str'))

    #Target variable is also a categorical so convert it
    fullData["TEST_STATUS"] = number.fit_transform(fullData["TEST_STATUS"].astype('str'))

    train=fullData[fullData['_Type']=='Train']
    test=fullData[fullData['_Type']=='Test']

    train['is_train'] = np.random.uniform(0, 1, len(train)) <= .75
    Train, Validate = train[train['is_train']==True], train[train['is_train']==False]

    features = list(set(cat_cols))


    x_train = Train[list(features)].values
    y_train = Train["TEST_STATUS"].values
    x_validate = Validate[list(features)].values
    y_validate = Validate["TEST_STATUS"].values
    x_test=test[list(features)].values

    random.seed(100)
    rf = RandomForestClassifier(n_estimators=1000)
    rf.fit(x_train, y_train)

    status = rf.predict_proba(x_validate)
    final_status = rf.predict_proba(x_test)
    test["TEST_STATUS"]=final_status[:,1]
    test.to_csv('data/prediction_model_output.csv',columns=['TEST_ID', 'TestCase','TEST_STATUS', 'Cosine','Effort'])


    #-------------------






    output = []
    fieldnames = ('TEST_ID', 'TestCase','TEST_STATUS','Effort')



    #convert csv to json
    csvfilename = 'data/prediction_model_output.csv'
    jsonfilename = csvfilename.split('.')[0] + '.json'
    csvfile = open(csvfilename, 'r')
    jsonfile = open(jsonfilename, 'w')
    reader = csv.DictReader(csvfile)

    for each in reader:
        row = {}
        for field in fieldnames:
            row[field] = each[field]
        output.append(row)





    json.dump(output, jsonfile, indent=2, sort_keys=True)




    #print(result_df)
    print('Output saved!')
    return Response(output)



@api_view(['Post'])
def dsvalue_cosine(request):
    # file=request.FILES['file']
    # print("printing the file ===>",request.FILES,type(request.FILES))
    


    text2=request.data.get('dsvalue',None)
    if not text2:
        return Response("need dsvalue data",status=400)
    print("printing the text2 ===>",text2)
    data=pd.read_excel('./../sample.xlsx',header=None)
    print(data)
    final_data={'string':[],'cosine':[]}
    
   # print("asdfasdfasdfasdf",len(data.count()))
    
    for i in data[1]:
        text1=i
        
        vector1=text_to_vector(text1)
        vector2=text_to_vector(text2)
        cosine =get_cosine(vector1,vector2)
        final_data['string'].append(i)
        final_data['cosine'].append(cosine)
        
    temp_ll=['cosine']
    temp_ll.extend(final_data['cosine'])
    final_dataframe=pd.DataFrame(data=final_data)

    #print(temp_ll)
    data[len(data.count())]=pd.Series(temp_ll)
    # data.insert(loc=len(data.count()),column=str(len(data.count())),value=temp_ll)
    #print(data[4])
    
    # final_dataframe.to_excel("Output.xlsx")
    #conversion of xlsx to json
    # os.remove('Output.xlsx')
    
    d={}
    for i in range(len(data.count())):
        
        dont=False
        for j in data[i]:
            
            if not dont:
                temp=j
                d[temp]=[]
                dont=True

            else:
                d[temp].append(j)
        # print("dfasdfasdfasdfasdf ===================>",d)

    #print("dfasdfasdfasdfasdf ===================>",d)
    key_names=[]
    
    for i in d:
        key_names.append(i)
    final=[]
    for i in range(len(d[key_names[0]])):
        temp_d={}
        for j in key_names:
            temp_d[j]=d[j][i]
        final.append(temp_d)



    return Response(final)


@api_view(['Get'])
def exc_values(request):
    data=pd.read_excel('./../sample.xlsx',header=None)
    print(len(data.count()),type(data.count()))
    d={}
    for i in range(len(data.count())):
        dont=False
        for j in data[i]:
            
            if not dont:
                temp=j
                d[temp]=[]
                dont=True

            else:
                d[temp].append(j)
    key_names=[]
    for i in d:
        key_names.append(i)
    final=[]
    for i in range(len(d[key_names[0]])):
        temp_d={}
        for j in key_names:
            temp_d[j]=d[j][i]
        final.append(temp_d)


    print(d)
    return Response(final)






from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView

class Index(APIView):
    def get(self,request,*args,**kwargs):
     return render(request,'index.html')
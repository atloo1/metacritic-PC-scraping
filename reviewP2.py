import pandas as pd
from collections import Counter

columnOrder = ['url', 'title', 'meanCriticReview', 'meanUserReview', 'numCriticReviews', 'numUserReviews',
               'fractionUserPositive', 'fractionUserMixed', 'fractionUserNegative', 'fractionCriticPositive',
               'fractionCriticMixed', 'fractionCriticNegative', 'developer', 'publisher', 'genres', 'releaseDate',
               'esrb', 'scrapyStatus', 'inspect']
data = pd.read_csv('inspect.csv')[columnOrder].set_index('url')    #parse,reorder,set index
errorTally = []
accuracy = 0.001    #the acceptable +/- tolerance of fields that should sum to unity
if False not in list(pd.isnull(data['inspect'])): data.iloc[:,-1] = ''    #make NaN empty strings for null inspect field
else: exit('\"Inspect\" field is not empty. Have you addressed them and cleared the field?')

#test for fields that should sum to 1, w/ room to accomodate float precision
unityFields = [columnOrder[6:9]] + [columnOrder[9:12]]  #critic and user fractions
for source in unityFields:
    subset = pd.DataFrame()
    for index,row in data[pd.notnull(data[source[0]])].iterrows():
        total = sum([i for i in row[source]])
        if abs(1-total) > accuracy:
            subset = subset.append(row)
    if len(subset) > 0:
        subset = subset[columnOrder[1:]]    #iterrows messes up the order for some reason
        subset.iloc[:, -1] += ', ' + str(source) + ' don\'t sum to 1'    #fields not summing to 1
    data.update(subset)
    errorTally += ['Fraction fields not summing to 1'] * len(subset)

    #the same row should have all 3 fields null
    nullFieldIndices = [i for lists in [list((data[pd.isnull(data[field])].index)) for field in source] for i in lists]
    subsetIndices = [index for index, count in Counter(nullFieldIndices).items() if count != 3]
    subset = data[data.index.isin(subsetIndices)]
    subset.iloc[:, -1] += ', ' + str(source) + ' not all null'  #some but not all fields are null
    data.update(subset)
    errorTally += ['not entirely null Fraction fields'] * len(subset)

#trim leading commas in inspect col & report error tally
for i in range(len(data)):
    if len(data.iloc[i, -1]) > 0: data.iloc[i, -1] = data.iloc[i, -1][2:]
for error, count in Counter(errorTally).items(): print(error + ': ' + str(count))
print('total errors: ' + str(len(errorTally)) + ' among ' + str(len(data)) + ' entries')

data.to_csv('inspect_revised.csv')
import pandas as pd
from collections import Counter

columnOrder = ['url', 'title', 'meanCriticReview', 'meanUserReview', 'numCriticReviews', 'numUserReviews',
               'fractionUserPositive', 'fractionUserMixed', 'fractionUserNegative', 'fractionCriticPositive',
               'fractionCriticMixed', 'fractionCriticNegative', 'developer', 'publisher', 'genres', 'releaseDate',
               'esrb', 'scrapyStatus']

data = pd.read_csv('data_initial.csv')[columnOrder].set_index('url')    #parse,reorder,set index
data['inspect'] = ''  # new col for informed manual inspection
errorTally = []

#todo iterate over df w/ df.iterrows() would be slicker; remember to reorder subset[colOrder]
#test for 0 or positive int fields
positiveIntCols = ['numCriticReviews', 'numUserReviews', 'scrapyStatus','meanCriticReview', 'meanUserReview']
for col in positiveIntCols:
    if col not in positiveIntCols[-2:]: #mean_Review can be null
        subset = data[pd.isnull(pd.to_numeric(data[col], errors='coerce', downcast='integer'))]  # handle nulls first
        subset.iloc[:, -1] += ', null ' + col  # null mean_Reviews are ok
        errorTally += ['null ' + col]*len(subset)
        data.update(subset)

    subset = data[pd.notnull(pd.to_numeric(data[col], errors='coerce', downcast='integer'))]    #handle non nulls 2nd
    for i in range(len(subset)):
        if float(subset[col][i])%1 != 0:
            subset.iloc[i, -1] += ', non int ' + col  # not an int
            errorTally += ['non int ' + col]
        elif float(subset[col][i]) < 0:
            subset.iloc[i, -1] += ', negative ' + col  # negative value
            errorTally += ['negative ' + col]
    data.update(subset)

#test for positive float fields
positiveFloatCols = ['fractionUserPositive', 'fractionUserMixed', 'fractionUserNegative', 'fractionCriticPositive',
               'fractionCriticMixed', 'fractionCriticNegative']
for col in positiveFloatCols:
    subset = data[pd.notnull(pd.to_numeric(data[col], errors = 'coerce', downcast = 'float'))]  #nulls checked in p2
    for i in range(len(subset)):
        value = pd.to_numeric(subset[col][i], errors = 'coerce', downcast = 'float')
        if value > 1 or value < 0:
            subset.iloc[i,-1] += ', impossible value of ' + col   #not a [0,1] bounded float
            errorTally += ['impossible value of ' + col]
    data.update(subset)

#test for datetime field
for i in range(len(data)):
    date = pd.to_datetime(data['releaseDate'][i], format='%Y-%m-%d', errors='coerce')
    if type(date) == pd.tslib.NaTType:
        data.iloc[i, -1] += ', releaseDate not a datetime'
        errorTally += ['releaseDate not a datetime']

#test for scrapyStatus == 200
subset = data[pd.notnull(data['scrapyStatus'])]
subset = subset[subset['scrapyStatus'] != 200]   #!= 200 value
subset = subset.append(data[pd.isnull(data['scrapyStatus'])])    #null value
subset.iloc[:, -1] += ', scrapyStatus != 200'
errorTally += ['scrapyStatus != 200']*len(subset)
data.update(subset)

#test for special chars in string fields
stringCols = ['title','developer', 'publisher']
for col in stringCols:
    subset = data[pd.isnull(data[col])]
    subset.iloc[:, -1] += ', ' + col + ' is null'    #null value
    errorTally += [col + ' is null'] * len(subset)
    data.update(subset)
    # todo more elegant to append, add error code to only new members and update once
    subset = data[pd.notnull(data[col])]
    subset = subset[subset[col].str.contains(r'[^a-zA-Z0-9\s\.\:\-\+\_\,\.\!\'\(\)\`\/\#\&\*\~\"\|\?\%\@\$\[\]\{\}]')]
    subset.iloc[:, -1] += ', special char in ' + col    #special char present
    errorTally += ['special char in ' + col] * len(subset)
    data.update(subset)

#test for duplicate titles
if len(list(data['title'])) != len(set(data['title'])):
    subset = data[data['title'].duplicated(keep=False)]
    subset.iloc[:,-1] += ', duplicate title'
    data.update(subset)
    errorTally += ['duplicate title'] * len(subset)

#trim leading commas in inspect col & report error tally
for i in range(len(data)):
    if len(data.iloc[i, -1]) > 0: data.iloc[i, -1] = data.iloc[i, -1][2:]
for error, count in Counter(errorTally).items(): print(error + ': ' + str(count))
print('total errors: ' + str(len(errorTally)) + ' among ' + str(len(data)) + ' entries')

data.to_csv('inspect.csv')
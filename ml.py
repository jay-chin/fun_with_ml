import re
import os
import random
from collections import Counter
from emlx import Emlx

def has_valid_date(text):
    # regular expression to match dates in format: 2010-08-27 and 2010/08/27
    date_reg_exp1 = re.compile('\d{4}[-/.]\d{2}[-/.]\d{2}')
    # regular expression to match dates in format: 27-08-2010 and 27/08/2010
    date_reg_exp2 = re.compile('\d{2}[-/.]\d{2}[-/.]\d{4}')

    if date_reg_exp1.search(text) or date_reg_exp2.search(text):
        return True
    else:
        return False

def getwords(txt):
    splitter = re.compile('\\W*')
    words = [ s.lower() for s in splitter.split(txt)
                if len(s) > 2 and len(s) < 20 ]
    return dict([(w, 1) for w in words])

def translate_non_alphanumerics(to_translate, translate_to=u''):
    not_letters_or_digits = u'!"#%\'()*+,-./:;<=>?@[\]^_`{|}~'
    translate_table = dict((ord(char), translate_to) for char in not_letters_or_digits)
    return to_translate.translate(translate_table)

def strip_punctuation(text): 
    ''' 
    Strips punctuation for unicode text
    '''
    regex = re.compile(ur"\p{P}+") 
    return re.sub(regex, " ", text)

def strip_nonletters(text): 
    ''' 
    Strips punctuation for unicode text
    '''
    regex = re.compile(ur"[^a-zA-Z]") 
    return re.sub(regex, " ", text)

def preprocess(text):
    '''
    Break up the words in the text and lemmatize them
    e.g. lemmatize will link the words price and prices since they are the same.
    '''
    from nltk import word_tokenize, WordNetLemmatizer
    from nltk.corpus import stopwords
    import string
    
    # Strip punctuation
    t = strip_punctuation(text)
    t = strip_nonletters(t)

    # Remove stopwords
    stoplist = stopwords.words('english') # list of stopwords, e.g. 'in', 'at', 'is', 'the'
    words = [word.lower() for word in word_tokenize(t) if word not in stoplist]

    # Lemmatize
    res = []
    for word in words:
        try:
            res.append(WordNetLemmatizer().lemmatize(word))
        except UnicodeDecodeError: # Ignore UnicodeDecode errors
            pass
    return res

def get_features(text, bow=True):
    if bow: # Bag-of-words uses frequency of words
        return {word: count for word, count in Counter(preprocess(text)).items()}
    else: # Just test for occurance of words
        return {word: True for word in preprocess(text)}

def main():
    training_dir = '/Users/jaychin/Playground/mail_data'
    all_emails = []
    for dirName, subdirList, fileList in os.walk(training_dir):
        for fname in fileList:
            file_path = os.path.join(dirName, fname)
            if dirName.endswith('not_flights'):
                all_emails.append((file_path, 'flights'))
            else:
                all_emails.append((file_path, 'not_flights'))
            #print('\tProcessing %s' % file_path)
   
    # let's shuffle them first then slice them up
    random.shuffle(all_emails)
    all_features = []
    for (email_path, label) in all_emails:
        e = Emlx(email_path)
        email_text = e.msg_data['From'] + ' ' + "\n".join(e.mime_payload)
        all_features.append((get_features(email_text, bow=True), label))
        print "Processed %s" % email_path

    # We want to split our data into training sets and testing sets with a ratio of 70:30
    train_size = int(len(all_features) * 0.7)
    train_set = all_features[:train_size]
    test_set = all_features[train_size:]

    # Let's print some stats for our classifier
    from nltk import NaiveBayesClassifier, classify
    classifier = NaiveBayesClassifier.train(train_set)
    print str(classify.accuracy(classifier, train_set))
    print str(classify.accuracy(classifier, test_set))
    classifier.show_most_informative_features(20)

    # Walk through our mail directory and start classifying
    # Print From and Subject lines for those that we identified as possible flights
    mail_dir = '/Users/jaychin/Library/Mail/V3/322B20BE-A01A-46E6-A7E1-F5F2CFA0FDAD'
    for dirName, subdirList, fileList in os.walk(mail_dir):
        for fname in fileList:
            file_path = os.path.join(dirName, fname)
            if fname.endswith('.emlx'):
                #print "Processing %s" % file_path
                e = Emlx(file_path)
                email_text = e.msg_data['From'] + "\n".join(e.mime_payload)
                if classifier.classify(get_features(email_text, bow=True)) == 'flights':
                    print "From : %s, subject = %s" % (e.msg_data['From'], e.msg_data['Subject'])


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs

import math;
import os;
import sys;


def main(args):
    """This program calculates, in response to a given query, the score
    of each document in a given collection"""
    
    options = {}

    print 'Welcome to the vectorial queryer'


    # We ask for the relative path and the theme words
    try:
        while True:
            path = raw_input('Enter relative path of the collection\n--> ')
            if (path.__len__() > 0):
                    break
            print 'Please enter a path'

        while True:
            theme = raw_input('Enter keywords (query) for the crawler \
(separated by a space)\n--> ')
            if (theme.__len__() > 0):
                    break
            print 'Please enter keywords (theme)'
 

    except EOFError:
        print '\nCaught EOF, exiting'
        sys.exit(1)

    print('Indexing...')


    # Separate all the theme words
    theme = [x.lower() for x in theme.split()]
    # To avoid duplicates
    theme = list(set(theme))

    # Dictionary containing all the words with their df
    theme_df_dict = {}
    # Dictionary containing all documents' name along with their score
    result_dict = {}

    # Absolute path of the collection
    collection_path = os.path.join(os.getcwd(),path)

    #List of files in the collection
    fileList = [b for b in os.listdir(collection_path) if os.path.isfile(os.path.join(collection_path,b))]


    # Lets calculate the df for all theme words
    for filename in fileList:

        # We open the file and separate all the words bigger than 3 characters
        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        # Now we look for theme words and change the df accordingly
        for term in theme:

            if fileWords.__contains__(term):
                # If the word has already been found, we increment its df.
                # Otherwise an exception is raised and we initialize it
                try:
                    theme_df_dict[term] += 1
                except KeyError:
                    theme_df_dict[term] = 1

        currentFile.close()


    print("Finished calculating the DF for the keywords. Now calculating scores \
for each document")

    theme_length = len(theme)

    # Now lets calculate the score (cosinus) for each document
    for filename in fileList:

        # We open the file and separate all the words bigger than 3 characters        
        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]


        # And now calculation of the vectorial model's cosinus
        inner_product = 0
        page_vector_norm = 0

        # We go through each theme word and calculate the tf.idf, the
        # inner_product and the page_vector_norm
        for term in theme:
            tf = fileWords.count(term)

            if tf>0:
                df = theme_df_dict[term]
                idf = 1./df
                weight = tf*idf

                inner_product += weight / theme_length
                page_vector_norm += (tf * idf)**2


        page_vector_norm = math.sqrt(page_vector_norm)

        if page_vector_norm == 0:
            score = 0

        else:
            # Classic similarity formula. Cosinus angle between our page
            # vector and the theme vector (filled with 1/len(theme))
            score = float(inner_product) / (page_vector_norm * 1./math.sqrt(theme_length))
        
        # We add our score in the dictionary next to the filename
        result_dict[filename]=score

        currentFile.close()

    print("***DONE***")
    print("")

    print("Score for each document:")
    print(result_dict)
    return result_dict


if __name__ == '__main__':
   main(sys.argv)

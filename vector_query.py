#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs

import math;
import os;
import sys;


def main(args):
    
    options = {}

    print 'Welcome to the vectorial queryer'

    try:
        while True:
            path = raw_input('Enter relative path of the collection\n--> ')
            if (path.__len__() > 0):
                    break
            print 'Please enter a path'

        while True:
            theme = raw_input('Enter keywords (theme) for the crawler\n--> ')
            if (theme.__len__() > 0):
                    break
            print 'Please enter keywords (theme)'
 

    except EOFError:
        print '\nCaught EOF, exiting'
        sys.exit(1)

    print('Indexing...')


    theme = [x.lower() for x in theme.split()]
    # To avoid duplicates
    theme = list(set(theme))

    theme_df_dict = {}
    index_dict = {}
    result_dict = {}

    collection_path = os.path.join(os.getcwd(),path)

    fileList = [b for b in os.listdir(collection_path) if os.path.isfile(os.path.join(collection_path,b))]

    for filename in fileList:

        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        for term in theme:

            if fileWords.__contains__(term):
                # If the word has already been found, we increment its df.
                # Otherwise an exception is raised and we initialize it
                try:
                    theme_df_dict[term] += 1
                except KeyError:
                    theme_df_dict[term] = 1

        currentFile.close()


    print("Finished calculating the DF for the keywords. Now calculating scores
          for each document")

    theme_length = len(theme)

    for filename in fileList:

        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        file_vector = []

        inner_product = 0
        page_vector_norm = 0

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

        result_dict[filename]=score

        currentFile.close()

    print("Score for each document:")
    print(result_dict)
    return result_dict


if __name__ == '__main__':
   main(sys.argv)

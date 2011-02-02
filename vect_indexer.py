#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs


import os;
import sys;


def main(args):
    """This program indexes a given collection by calculating the vector of scores
    for each document"""
    
    options = {}

    print 'Welcome to the vectorial indexer'

    # We ask where is the collection (relative path)
    try:
        while True:
            path = raw_input('Enter relative path of the collection\n--> ')
            if (path.__len__() > 0):
                    break
            print 'Please enter a path'

    except EOFError:
        print '\nCaught EOF, exiting'
        sys.exit(1)

    print('Indexing...')

    # Dictionary containing all the words with their df    
    vocabulary_df_dict = {}
    # Dictionary containing all documents' name along with their score    
    index_dict = {}

    # Absolute path of the collection
    collection_path = os.path.join(os.getcwd(),path)

    # List of all the files in the collection
    fileList = [b for b in os.listdir(collection_path) if os.path.isfile(os.path.join(collection_path,b))]


    # Lets calculate the df for every term (longer than 3 characters) of every document
    for filename in fileList:

        # We open the file and separate all the words bigger than 3 characters        
        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        # We initialise or increment the df for each term in the document
        for word in fileWords:

            # If the word has already been found, we increment its df.
            # Otherwise an exception is raised and we initialize it
            try:
                vocabulary_df_dict[word] += 1
            except KeyError:
                vocabulary_df_dict[word] = 1

        currentFile.close()

    print("Finished calculating the DF. Now really indexing...")

    # Now lets calculate the tf.idf for each term in the dictionary
    for filename in fileList:

        # We open the file and separate all the words bigger than 3 characters        
        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        # We initialise the score vector
        file_vector = []

        # For each term in the dictionary, we add the tf.idf in the vector
        for (term,df) in vocabulary_df_dict.items():
            tf = float(fileWords.count(term))

            file_vector += [tf/df]

            # We add the filename with its score vector in the final
            # dictionary
            index_dict[filename] = file_vector

        currentFile.close()

    print("***DONE***")
    print("")

    print("Score vector for each document:")
    print(index_dict)
    print("Term order:")
    print(vocabulary_df_dict.keys())


if __name__ == '__main__':
   main(sys.argv)


    

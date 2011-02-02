#!/usr/bin/env python
# -*- coding: utf-8 -*-

# libs


import os;
import sys;


def main(args):
    
    options = {}

    try:
        while True:
            path = raw_input('Enter relative path of the collection\n--> ')
            if (path.__len__() > 0):
                    break
            print 'Please enter a path'

    except EOFError:
        print '\nCaught EOF, exiting'
        sys.exit(1)

    print 'Welcome to the vectorial indexer'
    print('Indexing...')

    vocabulary_df_dict = {}
    index_dict = {}

    collection_path = os.path.join(os.getcwd(),path)
    print(collection_path)

    fileList = [b for b in os.listdir(collection_path) if os.path.isfile(os.path.join(collection_path,b))]

    for filename in fileList:

        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        for word in fileWords:

            # If the word has already been found, we increment its df.
            # Otherwise an exception is raised and we initialize it
            try:
                vocabulary_df_dict[word] += 1
            except KeyError:
                vocabulary_df_dict[word] = 1

        currentFile.close()

    print("Finished calculating the DF. Now really indexing")

    for filename in fileList:

        currentFile = open(os.path.join(collection_path ,filename));
        fileWords = currentFile.read().split();
        fileWords = [x.lower() for x in fileWords if x.__len__()>3]

        file_vector = []

        for (term,df) in vocabulary_df_dict.items():
            tf = float(fileWords.count(term))

            file_vector += [tf/df]

            index_dict[filename] = file_vector

        currentFile.close()

    print(index_dict)
    print(vocabulary_df_dict.keys())


if __name__ == '__main__':
   main(sys.argv)


    

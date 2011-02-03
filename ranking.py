# -*- coding: utf-8 -*-

from data_utils import ArrayQueue



page_rank_queue = ArrayQueue()



class PageRank():
    """Computes the PageRank algorithm on the pages list given in the
    constructor."""
    def __init__(self):
        link_list = page_rank_queue.get_copy()
        # Rk vector
        self._scores = []
        # dictionary to map link to its index in the matrix
        self._link_dict = {}
        # transition matrix for the page rank algorithm
        self._transition_matrix = []
        self._links_number = link_list.__len__()
        print self._links_number

        i = 0
        # initializes the transition matrix
        for link,_ in link_list:
            self._transition_matrix.append([])
            for j in xrange(self._links_number):
                # initializes the matrix with zeros
                self._transition_matrix[i].append(0)
            # initializing Rk vector with equal probability
            self._scores.append(1/float(self._links_number))
            # correspondance between link and position in the vector
            self._link_dict[link] = i
            i += 1

        self._build_initial_matrix(link_list)


    def _build_initial_matrix(self, target_list):
        # initializes the transition matrix
        for link, targets in target_list:
            # update outgoing row, and incoming col
            target_len = targets.__len__()
            link_pos = self._link_dict[link]
            for target in targets:
                try:
                    # no zero division possible, if len=0 we don't go 
                    # into the loop
                    self._transition_matrix[link_pos]\
[self._link_dict[target]] = 0.8/target_len + 0.2/self._links_number
                    # with a damping factor of 0.8
                except KeyError:
                    # url wasn't visited, passing
                    continue





    def _compute_rank(self, previous_vector):
        # one step of the relaxation
        new_vector = []
        for i in xrange(self._links_number):
            step_sum = 0
            for j in xrange(self._links_number):
                step_sum += self._transition_matrix[i][j] * previous_vector[j]
            new_vector.append(step_sum)
        return new_vector

    
    def get_top10(self):
        """Returns the top 10 for the page rank algorithm for the urls given at
        the initialization of the class. It is a list of tuples, containing the
        score in first position, and the link in second."""
        # computes the algorithm 50 times, an improvement would be to check the
        # difference between two computations against a rate
        for i in xrange(50):
            self._scores = self._compute_rank(self._scores)

        scores = []
        # iterates through the score vector to build the final result
        for link, pos in self._link_dict.items():
            scores.append((self._scores[pos], link))

        # sorts in place and returns the ten first scores
        scores.sort(reverse=True)
        return scores[:10]



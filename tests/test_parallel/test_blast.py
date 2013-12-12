#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2012, The QIIME project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "1.8.0"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"
__status__ = "Development"

from shutil import rmtree
from glob import glob
from os import getenv
from os.path import basename, exists, join
from tempfile import NamedTemporaryFile
from cogent import LoadSeqs
from cogent.util.unit_test import TestCase, main
from cogent.util.misc import remove_files, create_dir
from qiime.util import (get_qiime_temp_dir,
                        get_tmp_filename)
from qiime.test import initiate_timeout, disable_timeout
from qiime.parse import fields_to_dict

from qiime.parallel.blast import ParallelBlaster

class ParallelBlasterTests(TestCase):

    def setUp(self):
        """ """
        self.files_to_remove = []
        self.dirs_to_remove = []

        tmp_dir = get_qiime_temp_dir()
        self.test_out = get_tmp_filename(tmp_dir=tmp_dir,
                                         prefix='qiime_parallel_blaster_tests_',
                                         suffix='',
                                         result_constructor=str)
        self.dirs_to_remove.append(self.test_out)
        create_dir(self.test_out)

        self.tmp_seq_filepath = get_tmp_filename(tmp_dir=self.test_out,
            prefix='qiime_parallel_blaster_tests_input',
            suffix='.fasta')
        seq_file = open(self.tmp_seq_filepath, 'w')
        seq_file.write(blast_test_seqs)
        seq_file.close()
        self.files_to_remove.append(self.tmp_seq_filepath)

        self.reference_seqs_file = NamedTemporaryFile(
            prefix='qiime_parallel_blaster_tests_ref_seqs',
            suffix='.fasta',dir=tmp_dir)
        self.reference_seqs_file.write(blast_ref_seqs)
        self.reference_seqs_file.seek(0)

        initiate_timeout(60)

    def tearDown(self):
        """ """
        disable_timeout()
        remove_files(self.files_to_remove)
        # remove directories last, so we don't get errors
        # trying to remove files which may be in the directories
        for d in self.dirs_to_remove:
            if exists(d):
                rmtree(d)

    def test_parallel_blaster(self):
        """Test ParallelBlaster functions as expected."""
        params = {'refseqs_path':self.reference_seqs_file.name,
          'disable_low_complexity_filter':False,
          'e_value':0.001,
          'num_hits':1,
          'word_size':30,
          'suppress_format_blastdb':False,
          'blastmat_dir':None
        }
        
        app = ParallelBlaster()
        r = app(self.tmp_seq_filepath,
                self.test_out,
                params,
                job_prefix='BLASTTEST',
                poll_directly=True,
                suppress_submit_jobs=False)

        # Basic sanity checks: we should get two blast hits (lines). We ignore
        # all of the comments in the file. Each line should have 12 fields
        # separated by tabs.
        results = [line for line in open(glob(
                   join(self.test_out, '*_blast_out.txt'))[0], 'U') if not
                   line.startswith('#')]
        self.assertEqual(len(results), 2)
        self.assertEqual(len(results[0].split('\t')), 12)
        self.assertEqual(len(results[1].split('\t')), 12)

blast_test_seqs = \
""">11472286
GATGAACGCTGGCGGCATGCTTAACACATGCAAGTCGAACGGAACACTTTGTGTTTTGAGTTAATAGTTCGATAGTAGATAGTAAATAGTGAACACTATGAACTAGTAAACTATTTAACTAGAAACTCTTAAACGCAGAGCGTTTAGTGGCGAACGGGTGAGTAATACATTGGTATCTACCTCGGAGAAGGACATAGCCTGCCGAAAGGTGGGGTAATTTCCTATAGTCCCCGCACATATTTGTTCTTAAATCTGTTAAAATGATTATATGTTTTATGTTTATTTGATAAAAAGCAGCAAGACAAATGAGTTTTATATTGGTTATACAGCAGATTTAAAAAATAGAATTAGGTCTCATAATCAGGGAGAAAACAAATCAACTAAATCTAAAATACCTTGGGAATTGGTTTACTATGAAGCCTACAAAAACCAAACATCAGCAAGGGTTAGAGAATCAAAGTTGAAACATTATGGGCAATCATTAACTAGACTTAAGAGAAGAATTGGTTTTTGAGAACAAATATGTGCGGGGTAAAGCAGCAATGCGCTCCGAGAGGAACCTCTGTCCTATCAGCTTGTTGGTAAGGTAATGGCTTACCAAGGCGACGACGGGTAGCTGGTGTGAGAGCACGACCAGCCACACTGGGACTGAGACACGGCCCAGACTCCTACGGGAGGCAGCAGTGAGGAATTTTCCACAATGGGCGCAAGCCTGATGGAGCAATGCCGCGTGAAGGATGAAGATTTTCGGATTGTAAACTTCTTTTAAGTAGGAAGATTATGACGGTACTACTTGAATAAGCATCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGATGCAAGCGTTATCCGGAATTACTGGGCGTAAAGCGTGTGTAGGTGGTTTATTAAGTTAAATGTTAAATTTTCAGGCTTAACTTGGAAACCGCATTTAATACTGGTAGACTTTGAGGACAAGAGAGGCAGGCGGAATTAGCGGAGTAGCGGTGAAATGCGTAGATATCGCTAAGAACACCAATGGCGAAGGCAGCCTGCTGGTTTGCACCTGACACTGAGATACGAAAGCGTGGGGAGCGAACGGGATTAGATACCCCGGTAGTCCACGCCGTAAACGATGGTCACTAGCTGTTAGGGGCTCGACCCCTTTAGTAGCGAAGCTAACGCGTTAAGTGACCCGCCTGGGGAGTACGATCGCAAGATTAAAACTCAAAGGAATTGACGGGGACCCGCACAAGCGGTGGAACGTGAGGTTTAATTCGTCTCTAAGCGAAAAACCTTACCGAGGCTTGACATCTCCGGAAGACCTTAGAAATAAGGTTGTGCCCGAAAGGGAGCCGGATGACAGGTGCTGCATGGCTGTCGTCAGCTCGTGTTGTGAAATGTTCGGTTAAGTCCGTTAACGAGCGCAACCCTTGCTGTGTGTTGTATTTTTCACACAGGACTATCCTGGTCAACAGGGAGGAAGGTGGGGATGACGTCAAGTCAGCATGGCTCTTACGCCTCGGGCTACACTCGCGTTACAATGGCCGGTACAATGGGCTGCCAACTCGTAAGGGGGAGCTAATCCCATCAAAACCGGTCCCAGTTCGGATTGAGGGCTGCAATTCGCCCTCATGAAGTCGGAATCGCTAGTAACCGCGAATCAGCACGTCGCGGTGAATGCGTTCTCGGGTCTTGTACACACTGCCCGTCACACCACGAAAGTTAGTAACGCCCGAAGTGCCCTGTATGGGGTCCTAAGGTGGGGCTAGCGATTGGGGTG
>11472384
AGAGTTTGATCCTGGCTCAGATTGAACGCTGGCGGCATGCCTTACACATGCAAGTCGAACGGCAGCACGGGGGCAACCCTGGTGGCGAGTGGCGAACGGGTGAGTAATACATCGGAACGTGTCCTGTAGTGGGGGATAGCCCGGCGAAAGCCGGATTAATACCGCATACGCTCTACGGAGGAAAGGGGGGGATCTTAGGACCTCCCGCTACAGGGGCGGCCGATGGCAGATTAGCTAGTTGGTGGGGTAAAGGCCTACCAAGGCGACGATCTGTAGCTGGTCTGAGAGGACGACCAGCCACACTGGGACTGAGACACGGCCCAGACTCCTACGGGAGGCAGCAGTGGGGAATTTTGGACAATGGGGGCAACCCTGATCCAGCAATGCCGCGTGTGTGAAGAAGGCCTTCGGGTTGTAAAGCACTTTTGTCCGGAAAGAAAACGCCGTGGTTAATACCCGTGGCGGATGACGGTACCGGAAGAATAAGCACCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTCCGCTAAGACAGATGTGAAATCCCCGGGCTTAACCTGGGAACTGCATTTGTGACTGGCGGGCTAGAGTATGGCAGAGGGGGGTAGAATTCCACGTGTAGCAGTGAAATGCGTAGAGATGTGGAGGAATACCGATGGCGAAGGCAGCCCCCTGGGCCAATACTGACGCTCATGCACGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCCTAAACGATGTCAACTAGTTGTCGGGTCTTCATTGACTTGGTAACGTAGCTAACGCGTGAAGTTGACCGCCTGGGGAGTACGGTCGCAAGATTAAAACTCAAAGGAATTGACGGGGACCCGCACAAGCGGTGGATGATGTGGATTAATTCGATGCAACGCGAAAAACCTTACCTACCCTTGACATGTATGGAATCCTGCTGAGAGGTGGGAGTGCCCGAAAGGGAGCCATAACACAGGTGCTGCATGGCTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTGTCCCTAGTTGCTACGCAAGAGCACTCTAGGGAGACTGCCGGTGACAAACCGGAGGAAGGTGGGGATGACGTCAAGTCCTCATGGCCCTTATGGGTAGGGCTTCACACGTCATACAATGGTCGGAACAGAGGGTCGCCAACCCGCGAGGGGGAGCCAATCCCAGAAAACCGATCGTAGTCCGGATCGCACTCTGCAACTCGAGTGCGTGAAGCTGGAATCGCTAGTAATCGCGGATCAGCATGCCGCGGTGAATACGTTCCCGGGTCTTGTACACACCGCCCGTCACACCATGGGAGTGGGTTTTACCAGAAGTGGCTAGTCTAACCGCAAGGAGGACGGTCACCACGGTAGGATTCATGACTGGGGTGAAGTCGTAACAAGGTAGCCGTATCGGAAGGTGCGGCTGGATCACCTCCTTTCTCGAGCGAACGTGTCGAACGTTGAGCGCTCACGCTTATCGGCTGTGAAATTAGGACAGTAAGTCAGACAGACTGAGGGGTCTGTAGCTCAGTCGGTTAGAGCACCGTCTTGATAAGGCGGGGGTCGATGGTTCGAATCCATCCAGACCCACCATTGTCT
>11468680
TAAACTGAAGAGTTTGATCCTGGCTCAGATTGAACGCTGGCGGCATGCCTTACACATGCAAGTCGAACGGCAGCACGGGTGCTTGCACCTGGTGGCGAGTGGCGAACGGGTGAGTAATACATCGGAACATGTCCTGTAGTGGGGGATAGCCCGGCGAAAGCCGGATTAATACCGCATACGATCTACGGATGAAAGCGGGGGACCTTCGGGCCTCGCGCTATAGGGTTGGCCGATGGCTGATTAGCTAGTTGGTGGGGTAAAGGCCTACCAAGGCGACGATCAGTAGCTGGTCTGAGAGGACGACCAGCCACACTGGGACTGAGACACGGCCCAGACTCCTACGGGAGGCAGCAGTGGGGAATTTTGGACAATGGGCGAAAGCCTGATCCAGCAATGCCGCGTGTGTGAAGAAGGCCTTCGGGTTGTAAAGCACTTTTGTCCGGAAAGAAATCCTTGGCTCTAATACAGTCGGGGGATGACGGTACCGGAAGAATAAGCACCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGTGCGAGCGTTAATCGGAATTACTGGGCGTAAAGCGTGCGCAGGCGGTTTGCTAAGACCGATGTGAAATCCCCGGGCTCAACCTGGGAACTGCATTGGTGACTGGCAGGCTAGAGTATGGCAGAGGGGGGTAGAATTCCACGTGTAGCAGTGAAATGCGTAGAGATGTGGAGGAATACCGATGGCGAAGGCAGCCCCCTGGGCCAATACTGACGCTCATGCACGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCCTAAACGATGTCAACTAGTTGTTGGGGATTCATTTCCTTAGTAACGTAGCTAACGCGTGAAGTTGACCGCCTGGGGAGTACGGTCGCAAGATTAAAACTCAAAGGAATTGACGGGGACCCGCACAAGCGGTGGATGATGTGGATTAATTCGATGCAACGCGAAAAACCTTACCTACCCTTGACATGGTCGGAATCCCGCTGAGAGGTGGGAGTGCTCGAAAGAGAACCGGCGCACAGGTGCTGCATGGCTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTGTCCTTAGTTGCTACGCAAGAGCACTCTAAGGAGACTGCCGGTGACAAACCGGAGGAAGGTGGGGATGACGTCAAGTCCTCATGGCCCTTATGGGTAGGGCTTCACACGTCATACAATGGTCGGAACAGAGGGTTGCCAACCCGCGAGGGGGAGCTAATCCCAGAAAACCGATCGTAGTCCGGATTGCACTCTGCAACTCGAGTGCATGAAGCTGGAATCGCTAGTAATCGCGGATCAGCATGCCGCGGTGAATACGTTCCCGGGTCTTGTACACACCGCCCGTCACACCATGGGAGTGGGTTTTACCAGAAGTGGCTAGTCTAACCGCAAGGAGGACGGTCACCACGGTAGGATTCATGACTGGGGTGAAGTCGTAACAAGGTAGCCGTATCGGAAGGTGCGGCTGGATCACCTCCTTTCCAGAGCTATCTCGCAAAGTTGAGCGCTCACGCTTATCGGCTGTAAATTTAAAGACAGACTCAGGGGTCTGTAGCTCAGTCGGTTAGAGCACCGTCTTGATAAGGCGGGGGTCGTTGGTTCGAATCCAACCAGACCCACCATTGTCTG
>11458037
GACGAACGCTGGCGGCGTGCCTAACACATGCAAGTCGAACGGTTTCGAAGATCGGACTTCGAATTTCGAATTTCGATCATCGAGATAGTGGCGGACGGGTGAGTAACGCGTGGGTAACCTACCCATAAAGCCGGGACAACCCTTGGAAACGAGGGCTAATACCGGATAAGCTTGAGAAGTGGCATCACTTTTTAAGGAAAGGTGGCCGATGAGAATGCTGCCGATTATGGATGGACCCGCGTCTGATTAGCTGGTTGGTGGGGTAAAGGCCTACCAAGGCGACGATCAGTAGCCGGCCTGAGAGGGTGAACGGCCACACTGGGACTGAGACACGGCCCAGACTCCTACGGGAGGCAGCAGTGGGGAATCTTCCGCAATGGACGAAAGTCTGACGGAGCAACGCCGCGTGTATGATGAAGGTTTTCGGATTGTAAAGTACTGTCTATGGGGAAGAATGGTGTGCTTGAGAATATTAAGTACAAATGACGGTACCCAAGGAGGAAGCCCCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGGGCAAGCGTTGTCCGGAATTATTGGGCGTAAAGGGCGCGTAGGCGGATAGTTAAGTCCGGTGTGAAAGATCAGGGCTCAACCCTGAGAGTGCATCGGAAACTGGGTATCTTGAGGACAGGAGAGGAAAGTGGAATTCCACGTGTAGCGGTGAAATGCGTAGATATGTGGAGGAACACCAGTGGCGAAGGCGACTTTCTGGACTGTAACTGACGCTGAGGCGCGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCTGTAAACGATGAGTGCTAGGTGTAGAGGGTATCGACCCCTTCTGTGCCGCAGTTAACACAATAAGCACTCCGCCTGGGGAGTACGGCCGCAAGGTTGAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGACGCAACGCGAAGAACCTTACCAGGGCTTGACATCCTCTGAACTTGCTGGAAACAGGAAGGTGCCCTTCGGGGAGCAGAGAGACAGGTGGTGCATGGTTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAATCCCGCAACGAGCGCAACCCCTGTATTTAGTTGCTAACGCGTAGAGGCGAGCACTCTGGATAGACTGCCGGTGATAAACCGGAGGAAGGTGGGGATGACGTCAAATCATCATGCCCCTTATGTTCTGGGCTACACACGTGCTACAATGGCCGGTACAGACGGAAGCGAAGCCGCGAGGCGGAGCAAATCCGAGAAAGCCGGTCTCAGTTCGGATTGCAGGCTGCAACTCGCCTGCATGAAGTCGGAATCGCTAGTAATCGCAGGTCAGCATACTGCGGTGAATACGTTCCCGGGCCTTGTACACACCGCCCGTCACACCACGAAAGTCTGCAACACCCGAAGCCGGTGAGGTAACCGACTCGAGATTCGAGGCTCGAAGTTCGAGGATCGAAGTGTAAGCGAAATTAATAAGTCTTAGTAAAGCTAAAAAGCATTAAGACCGATAAGATGATCTTGCAATCGAACATCGAACATCGAATTTCGAACCTCGAGTTGGAGCTAGCCGTCGAAGGTGGGGCCGATAATTGGGGTG
>11469739
AGAGTTTGATCCTGGCTCAGGATGAACGCTGGCGGCGTGCCTAACACATGCAAGTCGAACGAGAAGCTAACTTCTGATTCCTTCGGGATGATGAGGTTAGCAGAAAGTGGCGAACGGGTGAGTAACGCGTGGGTAATCTACCCTGTAAGTGGGGGATAACCCTCCGAAAGGAGGGCTAATACCGCATAATATCTTTATCCCAAAAGAGGTAAAGATTAAAGATGGCCTCTATACTATGCTATCGCTTCAGGATGAGTCCGCGTCCTATTAGTTAGTTGGTGGGGTAATGGCCTACCAAGACGACAATGGGTAGCCGGTCTGAGAGGATGTACGGCCACACTGGGACTGAGATACGGCCCAGACTCCTACGGGAGACAGCAGTGGGGAATATTGCGCAATGGGGGAAACCCTGACGCAGCGACGCCGCGTGGATGATGAAGGCCCTTGGGTTGTAAAATCCTGTTCTGGGGGAAGAAAGCTTAAAGGTCCAATAAACCCTTAAGCCTGACGGTACCCCAAGAGAAAGCTCCGGCTAATTATGTGCCAGCAGCCGCGGTAATACATAAGGAGCAAGCGTTATCCGGAATTATTGGGCGTAAAGAGCTCGTAGGCGGTCTTAAAAGTCAGTTGTGAAATTATCAGGCTCAACCTGATAAGGTCATCTGAAACTCTAAGACTTGAGGTTAGAAGAGGAAAGTGGAATTCCCGGTGTAGCGGTGAAATGCGTAGATATCGGGAGGAACACCAGTGGCGAAGGCGGCTTTCTGGTCTATCTCTGACGCTGAGGAGCGAAAGCTAGGGGAGCAAACGGGATTAGATACCCCGGTAGTCCTAGCTGTAAACGATGGATACTAGGTGTGGGAGGTATCGACCCCTTCTGTGCCGTAGCTAACGCATTAAGTATCCCGCCTGGGGAGTACGGTCGCAAGGCTGAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGACGCAACGCGAAGAACCTTACCGGGACTTGACATTATCTTGCCCGTCTAAGAAATTAGATCTTCTTCCTTTGGAAGACAGGATAACAGGTGGTGCATGGTTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCACAACGAGCGCAACCCTTGTGCTTAGTTGCTAACTTGTTTTACAAGTGCACTCTAGGCAGACTGCCGCAGATAATGCGGAGGAAGGTGGGGATGACGTCAAATCATCATGCCCCTTACGTCCCGGGCTACACACGTGCTACAATGGCCTGTACAGAGGGTAGCGAAAGAGCGATCTTAAGCCAATCCCAAAAAGCAGGCCCCAGTTCGGATTGGAGGCTGCAACTCGCCTCCATGAAGTAGGAATCGCTAGTAATCGCGGATCAGCATGCCGCGGTGAATACGTTCCCGGGCCTTGTACACACCGCCCGTCACACCACGAAAGTTGGCGATACCTGAAGTTACTAGGCTAACCTGGCACTCAACTAAGTTCACTAACTTATTTGCTTAAAATAAGGCTTAATGTGCTTAGTTGAGTGCCGGGAGGCAGGTACCGAAGGTATGGCTGGCGATTGGGGTGAAGTCGTAACAAGGTGGAAA
>11469752
AGAGTTTGATCCTGGCTCAGGATGAACGCTGGCGGCGTGCCTAATACATGCAAGTCGAGCGGCAGCGAGTTCCTCACCGAGGTTCGGAACAGTTGACAGTAAACAGTTGACAGTAAACAGTAACTTCAGAAATGAAGCGGACTGTGAACTGTTTACTGTAACCTGTTAGCTATTATTTCGAGCTTTAGTGAGGAATGTCGGCGAGCGGCGGACGGCTGAGTAACGCGTAGGAACGTACCCCAAACTGAGGGATAAGCACCAGAAATGGTGTCTAATACCGCATATGGCCCAGCACCTTTTTTAATCAACCACGACCCTAAAATCGTGAATAATTGGTAGGAAAAGGTGTTGGGTTAAAGCTTCGGCGGTTTGGGAACGGCCTGCGTATGATTAGCTTGTTGGTGAGGTAAAAGCTCACCAAGGCGACGATCATTAGCTGGTCTGAGAGGATGATCAGCCAGACTGGGACTGAGACACGGCCCAGACTCCTACGGGAGGCAGCAGTAGGGAATCTTCCACAATGGGCGAAAGCCTGATGGAGCAACGCCGTGTGCAGGATGAAAGCCTTCGGGTCGTAAACTGCTTTTATATGTGAAGACTTCGACGGTAGCATATGAATAAGGATCGGCTAACTCCGTGCCAGCAGCCGCGGTCATACGGAGGATCCAAGCGTTATCCGGAATTACTGGGCGTAAAGAGTTGCGTAGGTGGCATAGTAAGTTGGTAGTGAAATTGTGTGGCTCAACCATACACCCATTACTAAAACTGCTAAGCTAGAGTATATGAGAGGTAGCTGGAATTCCTAGTGTAGGAGTGAAATCCGTANATATTAGGAGGAACACCGATGGCGTAGGCAGGCTACTGGCATATTACTGACACTAAGGCACGAAAGCGTGGGGAGCGAACGGGATTAGATACCCCGGTAGTCCACGCTGTAAACGATGGATGCTAGCTGTTATGAGTATCGACCCTTGTAGTAGCGAAGCTAACGCGTTAAGCATCCCGCCTGTGGAGTACGAGCGCAAGCTTAAAACATAAAGGAATTGACGGGGACCCGCACAAGCGGTGGAGCGTGTTGTTTAATTCGATGATAAGCGAAGAACCTTACCAAGGCTTGACATCCCTGGAATTTCTCCGAAAGGAGAGAGTGCCTTCGGGAATCAGGTGACAGGTGATGCATGGCCGTCGTCAGCTCGTGTCGTGAGATGTTTGGTTAAGTCCATTAACGAGCGCAACCCTTGTAAATAGTTGGATTTTTCTATTTAGACTGCCTCGGTAACGGGGAGGAAGGAGGGGATGATGTCAGGTCAGTATTTCTCTTACGCCTTGGGCTACAAACACGCTACAATGGCCGGTACAAAGGGCAGCCAACCCGCGAGGGGGAGCAAATCCCATCAAAGCCGGTCTCAGTTCGGATAGCAGGCTGAAATTCGCCTGCTTGAAGTCGGAATCGCTAGTAACGGTGAGTCAGCTATATTACCGTGAATACGTTCCCGGGTCTTGTACACACCGCCCGTCAAGGCATGAAAGTCATCAATACCTGACGTCTGGATTTATTCTGGCCTAAGGTAGGGGCGATGATTGGGCCTAAGTCGTAACAAGGTAA
>11460523
AGAGTTTGATCCTGGCTCAGAACGAACGCTGGCGGCGTGCTTAACACATGCAAGTCGAACGCGAAATCGGGCACTCAATTTTGCTTTTCAAACATTAACTGATGAAACGACCAGAGAGATTGTTCCAGTTTAAAGAGTGAAAAGCAGGCTTGAGTGCCTGAGAGTAGAGTGGCGCACGGGTGAGTAACGCGTAAATAATCTACCCCTGCATCTGGGATAACCCACCGAAAGGTGAGCTAATACCGGATACGTTCTTTTAACCGCGAGGTTTTAAGAAGAAAGGTGGCCTCTGATATAAGCTACTGTGCGGGGAGGAGTTTGCGTACCATTAGCTAGTTGGTAGGGTAATGGCCTACCAAGGCATCGATGGTTAGCGGGTCTGAGAGGATGATCCGCCACACTGGAACTGGAACACGGACCAGACTCCTACGGGAGGCAGCAGTGAGGAATATTGCGCAATGGGGGCAACCCTGACGCAGCGACGCCGCGTGGATGATGAAGGCCTTCGGGTCGTAAAATCCTGTCAGATGGAAAGAAGTGTTATATGGATAATACCTGTATAGCTTGACGGTACCATCAAAGGAAGCACCGGCTAACTCCGTGCCAGCAGCCGCGGTAATACGGAGGGTGCAAGCGTTGTTCGGAATTACTGGGCGTAAAGCGCGCGTAGGCGGTCTGTTATGTCAGATGTGAAAGTCCACGGCTCAACCGTGGAAGTGCATTTGAAACTGACAGACTTGAGTACTGGAGGGGGTGGTGGAATTCCCGGTGTAGAGGTGAAATTCGTAGATATCGGGAGGAATACCGGTGGCGAAGGCGACCACCTGGCCAGATACTGACGCTGAGGTGCGAAAGCGTGGGGAGCAAACAGGATTAGATACCCTGGTAGTCCACGCCGTAAACGATGTCAACTAGGTGTTGGGATGGTTAATCGTCTCATTGCCGGAGCTAACGCATTAAGTTGACCGCCTGGGGAGTACGGTCGCAAGATTAAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGTATGTGGTTTAATTCGACGCAACGCGCAGAACCTTACCTGGTCTTGACATCCCGAGAATCTCAAGGAAACTTGAGAGTGCCTCTTGAGGAACTCGGTGACAGGTGCTGCATGGCTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTGTCTTTAGTTGCCATCATTAAGTTGGGCACTCTAAAGAGACTGCCGGTGTCAAACCGGAGGAAGGTGGGGATGACGTCAAGTCCTCATGGCCTTTATGACCAGGGCTACACACGTACTACAATGGCATAGACAAAGGGCAGCGACATCGCGAGGTGAAGCGAATCCCATAAACCATGTCTCAGTCCGGATTGGAGTCTGCAACTCGACTCCATGAAGTTGGAATCGCTAGTAATCGTAGATCAGCATGCTACGGTGAATACGTTCCCGGGCCTTGTACACACCGCCCGTCACACCACGGGAGTTGGTTGTACCAGAAGCAGTTGAGCGAACTATTCGTAGACGCAGGCTGCCAAGGTATGATTGGTAACTGGGGTGAAGTCGTAACAAGGTAACC
>11460543
TGGTTTGATCCTGGCTCAGGACAAACGCTGGCGGCGTGCCTAACACATGCAAGTCGAACGAGAAGCCAGCTTTTGATTCCTTCGGGATGAGAAAGCAGGTAGAAAGTGGCGAACGGGTGAGTAACGCGTGGGTAATCTACCCTGTAAGTAGGGGATAACCCTCTGAAAAGAGGGCTAATACCGCATAATATCTTTACCCCATAAGAAGTAAAGATTAAAGATGGCCTCTGTATATGCTATCGCTTCAGGATGAGCCCGCGTCCTATTAGTTAGTTGGTAAGGTAATGGCTTACCAAGACCACGATGGGTAGCCGGTCTGAGAGGATGTACGGCCACACTGGGACTGAGATACGGCCCAGACTCCTACGGGAGGCAGCAGTGGGGAATATTGCGCAATGGGGGAAACCCTGACGCAGCGACGCCGCGTGGATGATGAAGGCCTTCGGGTTGTAAAATCCTGTTTTGGGGGACGAAACCTTAAGGGTCCAATAAACCCTTAAATTGACGGTACCCCAAGAGAAAGCTCCGGCTAATTATGTGCCAGCAGCCGCGGTAATACATAAGGAGCAAGCGTTGTCCGGAATTATTGGGCGTAAAGAGTTCGTAGGCGGTCTTAAAAGTCAGGTGTGAAATTATCAGGCTTAACCTGATACGGTCATCTGAAACTTTAAGACTTGAGGTTAGGAGAGGAAAGTGGAATTCCCGGTGTAGCGGTGAAATGCGTAGATATCGGGAGGAACACCAGTGGCGAAGGCGGCTTTCTGGCCTAACTCTGACGCTGAGGAACGAAAGCTAGGGGAGCAAACGGGATTAGATACCCCGGTAGTCCTAGCTGTAAACGATGGATACTAGGTGTGGGAGGTATCGACCCCTTCTGTGCCGWCACTAACGCATTAAGTATCCCGCCTGGGGAGTACGGTCGCAAGGCTAAAACTCAAAGGAATTGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGACGCAACGCGAAGAACCTTACCGGGGCTTGACATTGTCTTGCCCGTTTAAGAAATTAAATTTTCTTCCCTTTTAGGGAAGACAAGATAACAGGTGGTGCATGGTTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCACAACGAGCGCAACCCTTATTCTTAGTTGCTAGTTTGTTTACAAACGCACTCTAAAGAGACTGCCGCAGATAATGCGGAGGAAGGTGGGGATGACGTCAAATCATCATGCCCCTTACGTCCCGGGCTACACACGTGCTACAATGGCCTGTACAGAGGGTAGCGAAAGAGCGATCTCAAGCTAATCCCTTAAAACAGGTCTCAGTTCGGATTGGAGGCTGCAACTCGCCTCCATGAAGTCGGAATCGCTAGTAATCGCGGATCAGCATGCCGCGGTGAATACGTTCCCGGGCCTTGTACACACCGCCCGTCACACCATGAAAGTTGGCGATACCTGAAGTTACTGTGCTAACCCGGCACTCAACTAAGTACATTAAGTCTTATTTTAAGCTATTGTATTTAGTTGAGTGCCGGGAGGCAGGTACCTAAGGTATGGCTAGCGATTGGGGTGAAGTCGTAACAAGGTAGCCG
>11480235
TGGTTTGATCCTGGCTCAGGATTAACGCTGGCGGCGCGCCTTATACATGCAAGTCGAACGAGCCTTGTGCTTCGCACAAGGAAATTCCAAGCACCAAGCACCAAATCTCAAACAAATCCCAATGACCAAAATTCCAAAAACCTAAACATTTTAAATGTTTAGAATTTGGAAAATTGGAATTTGGAATTTATTTGTTATTTGGAATTTATGATTTGGGATTTTCTCGCGCGGAGANCNTNAGTGGCGAACGGGTGAGTAATACGTTGGTATCTACCCCAAAGTAGAGAATAAGCCCGAGAAATCGGGGTTAATACTCTATGTGTTCGAAAGAACAAAGACTTCGGTTGCTTTGGGAAGAACCTGCGGCCTATCAGCTTGTTGGTAAGGTAACGGCTTACCAAGGCTTTGACGGGTAGCTGGTCTGGGAAGACGACCAGCCACAATGGGACTTAGACACGGCCCATACTCCTACGGGAGGCAGCAGTAGGGAATCTTCGGCAATGCCCGAAAGGTGACCGAGCGACGCCGCGTAGAGGAAGAAGATCTTTGGATTGTAAACTCTTTTTCTCCTAGACAAAGTTCTGATTGTATAGGAGGAATAAGGGGTTTCTAAACTCGTGCCAGCAGAAGCGGTAATACGAGTGCCCCAAGCGTTATCCGGAATCATTGGGCGTAGAGCGTTGTATAGGTGGTTTAAAAAGTCCAAAATTAAATCTTTAGGCTCAACCTAAAATCTGTTTTGGAAACTTTTAGACTTGAATAAAATCGACGSGAGTGGAACTTCCAGAGTAGGGGTTACATCCGTTGATACTGGAAGGAACGCCGAAGGCGAAAGCAACTCGCGAGATTTTATTGACGCCGCGTACACGAAAGCGTGGGGAGCGAAAAGTATTAGATACACTTGTAGTCCACGCCGTAAACTATGGATACTAGCAATTTGAAGCTTCGACCCTTCAAGTTGCGGACTAACGCGTTAAGTATCTCGCCTGGGAAGTACGGCCGCAAGGCTAAAACTCAAAGGAATAGACGGGGGCCCGCACAAGCGGTGGAGCATGTGGTTTAATTCGACGATAAGCGTGGAACCTTACCAGGGCTTAGACGTACAGAGAATTCCTTGGAAACAAGGAAGTGCTTCGGGAACTCTGTACTCAGGTACTGCATGGCTGTCGTCAGTATGTACTGTGAAGCACTCCCTTAATTGGGGCAACATACGCAACCCCTATCCTAAGTTAGAAATGTCTTAGGAAACCGCTTCGATTCATCGGAGAGGAAGATGGGGACGACGTCAAGTCAGCATGGTCCTTGATGTCCTGGGCGACACACGTGCTACAATGGCTAGTATAACGGGATGCGTAGGTGCGAACCGAAGCTAATCCTTAAAAAACTAGTCTAAGTTCGGATTGAAGTCTGCAACTCGACTTCATGAAGCCGGAATCGCTAGTAACCGCAAATCAGCCACGTTGCGGTGAATACGTTCTCGGGCCTTGTACTCACTGCCCGTCACGTCAAAAAAGTCGGTAATACCCGAAGCACCCTTTTAAAGGGTTCTAAGGTAGGACCGATGATTGGGACGAAGTCGTAACAAGGTAGCCG
>11480408
AATTTAGCGGCCGCGAATTCGCCCTTGAGTTTGATCCTGGCTCAGGACGAACGCTGGCGGCGTGCTTAACACATGCAAGTCGAACGGGGATATCCGAGCGGAAGGTTTCGGCCGGAAGGTTGGGTATTCGAGTGGCGGACGGGTGAGTAACGCGTGAGCAATCTGTCCCGGACAGGGGGATAACACTTGGAAACAGGTGCTAATACCGCATAAGACCACAGCATCGCATGGTGCAGGGGTAAAAGGAGCGATCCGGTCTGGGGTGAGCTCGCGTCCGATTAGATAGTTGGTGAGGTAACGGCCCACCAAGTCAACGATCGGTAGCCGACCTGAGAGGGTGATCGGCCACATTGGAACTGAGAGACGGTCCAAACTCCTACGGGAGGCAGCAGTGGGGAATATTGGGCAATGGGCGAAAGCCTGACCCAGCAACGCCGCGTGAGTGAAGAAGGCCTTCGGGTTGTAAAGCTCTGTTATGCGAGACGAAGGAAGTGACGGTATCGCATAAGGAAGCCCCGGCTAACTACGTGCCAGCAGCCGCGGTAATACGTAGGGGGCGAGCGTTGTCCGGAATGACTGGGCGTAAAGGGCGTGTAGGCGGCCGTTTAAGTATGGAGTGAAAGTCCATTTTTCAAGGATGGAATTGCTTTGTAGACTGGATGGCTTGAGTGCGGAAGAGGTAAGTGGAATTCCCAGTGTAGCGGTGAAATGCGTAGAGATTGGGAGGAACACCAGTGGCGAAGGCGACTTACTGGGCCGTAACTGACGCTGAGGCGCGAAAGCGTGGGGAGCGAACAGGATTAGATACCCTGGTAGTCCACGCGGTAAACGATGAATGCTAGGTGTTGCGGGTATCGACCCCTGCAGTGCCGGAGTAAACACAATAAGCATTCCGCCTGGGGAGTACGGCCGCAAGGTTGAAACTCAAGGGAATTGACGGGGGCCCGCACAAGCAGCGGAGCATGTTGTTTAATTCGAAGCAACGCGAAGAACCTTACCAGGTCTTGACATCCAGTTAAGCTCATAGAGATATGAGGTCCCTTCGGGGGAACTGAGACAGGTGGTGCATGGTTGTCGTCAGCTCGTGTCGTGAGATGTTGGGTTAAGTCCCGCAACGAGCGCAACCCTTATGGTCAGTTACTAACGCGTGAAGGCGAGGACTCTGACGAGACTGCCGGGGACAACTCGGAGGAAGGTGGGGACGACGTCAAATCATCATGCCCCTTATGACCTGGGCTACAAACGTGCTACAATGGTGACTACAAAGAGGAGCGAGACTGTAAAGTGGAGCGGATCTCAAAAAAGTCATCCCAGTTCGGATTGTGGGCTGCAACCCGCCCACATGAAGTTGGAGTTGCTAGTAATCGCGGATCAGCATGCCGCGGTGAATACGTTCCCGGGCCTTGTACACACCGCCCGTCACACCATGGGAGTTGGGAGCACCCGAAGTCAGTGAGGTAACCGGAAGGAGCCAGCTGCCGAAGGTGAGACCGATGACTGGGGTGAAGTCGTAACAAGGTAGCCGTATCGGAAGGTGCGGCTGGATCACCTCCTTAAGGGCGAATTCGTTTAAACCTGCAGGACTAG
"""

blast_ref_seqs = \
"""
>AY800210
TTCCGGTTGATCCTGCCGGACCCGACTGCTATCCGGATGCGACTAAGCCATGCTAGTCTAACGGATCTTCGGATCCGTGGCATACCGCTCTGTAACACGTAGATAACCTACCCTGAGGTCGGGGAAACTCCCGGGAAACTGGGCCTAATCCCCGATAGATAATTTGTACTGGAATGTCTTTTTATTGAAACCTCCGAGGCCTCAGGATGGGTCTGCGCCAGATTATGGTCGTAGGTGGGGTAACGGCCCACCTAGCCTTTGATCTGTACCGGACATGAGAGTGTGTGCCGGGAGATGGCCACTGAGACAAGGGGCCAGGCCCTACGGGGCGCAGCAGGCGCGAAAACTTCACAATGCCCGCAAGGGTGATGAGGGTATCCGAGTGCTACCTTAGCCGGTAGCTTTTATTCAGTGTAAATAGCTAGATGAATAAGGGGAGGGCAAGGCTGGTGCCAGCCGCCGCGGTAAAACCAGCTCCCGAGTGGTCGGGATTTTTATTGGGCCTAAAGCGTCCGTAGCCGGGCGTGCAAGTCATTGGTTAAATATCGGGTCTTAAGCCCGAACCTGCTAGTGATACTACACGCCTTGGGACCGGAAGAGGCAAATGGTACGTTGAGGGTAGGGGTGAAATCCTGTAATCCCCAACGGACCACCGGTGGCGAAGCTTGTTCAGTCATGAACAACTCTACACAAGGCGATTTGCTGGGACGGATCCGACGGTGAGGGACGAAACCCAGGGGAGCGAGCGGGATTAGATACCCCGGTAGTCCTGGGCGTAAACGATGCGAACTAGGTGTTGGCGGAGCCACGAGCTCTGTCGGTGCCGAAGCGAAGGCGTTAAGTTCGCCGCCAGGGGAGTACGGCCGCAAGGCTGAAACTTAAAGGAATTGGCGGGGGAGCAC
>EU883771
TGGCGTACGGCTCAGTAACACGTGGATAACTTACCCTTAGGACTGGGATAACTCTGGGAAACTGGGGATAATACTGGATATTAGGCTATGCCTGGAATGGTTTGCCTTTGAAATGTTTTTTTTCGCCTAAGGATAGGTCTGCGGCTGATTAGGTCGTTGGTGGGGTAATGGCCCACCAAGCCGATGATCGGTACGGGTTGTGAGAGCAAGGGCCCGGAGATGGAACCTGAGACAAGGTTCCAGACCCTACGGGGTGCAGCAGGCGCGAAACCTCCGCAATGTACGAAAGTGCGACGGGGGGATCCCAAGTGTTATGCTTTTTTGTATGACTTTTCATTAGTGTAAAAAGCTTTTAGAATAAGAGCTGGGCAAGACCGGTGCCAGCCGCCGCGGTAACACCGGCAGCTCGAGTGGTGACCACTTTTATTGGGCTTAAAGCGTTCGTAGCTTGATTTTTAAGTCTCTTGGGAAATCTCACGGCTTAACTGTGAGGCGTCTAAGAGATACTGGGAATCTAGGGACCGGGAGAGGTAAGAGGTACTTCAGGGGTAGAAGTGAAATTCTGTAATCCTTGAGGGACCACCGATGGCGAAGGCATCTTACCAGAACGGCTTCGACAGTGAGGAACGAAAGCTGGGGGAGCGAACGGGATTAGATACCCCGGTAGTCCCAGCCGTAAACTATGCGCGTTAGGTGTGCCTGTAACTACGAGTTACCGGGGTGCCGAAGTGAAAACGTGAAACGTGCCGCCTGGGAAGTACGGTCGCAAGGCTGAAACTTAAAGGAATTGGCGGGGGAGCACCACAACGGGTGGAGCCTGCGGTTTAATTGGACTCAACGCCGGGCAGCTCACCGGATAGGACAGCGGAATGATAGCCGGGCTGAAGACCTTGCTTGACCAGCTGAGA
>EF503699
AAGAATGGGGATAGCATGCGAGTCACGCCGCAATGTGTGGCATACGGCTCAGTAACACGTAGTCAACATGCCCAGAGGACGTGGACACCTCGGGAAACTGAGGATAAACCGCGATAGGCCACTACTTCTGGAATGAGCCATGACCCAAATCTATATGGCCTTTGGATTGGACTGCGGCCGATCAGGCTGTTGGTGAGGTAATGGCCCACCAAACCTGTAACCGGTACGGGCTTTGAGAGAAGGAGCCCGGAGATGGGCACTGAGACAAGGGCCCAGGCCCTATGGGGCGCAGCAGGCACGAAACCTCTGCAATAGGCGAAAGCTTGACAGGGTTACTCTGAGTGATGCCCGCTAAGGGTATCTTTTGGCACCTCTAAAAATGGTGCAGAATAAGGGGTGGGCAAGTCTGGTGTCAGCCGCCGCGGTAATACCAGCACCCCGAGTTGTCGGGACGATTATTGGGCCTAAAGCATCCGTAGCCTGTTCTGCAAGTCCTCCGTTAAATCCACCCGCTTAACGGATGGGCTGCGGAGGATACTGCAGAGCTAGGAGGCGGGAGAGGCAAACGGTACTCAGTGGGTAGGGGTAAAATCCTTTGATCTACTGAAGACCACCAGTGGTGAAGGCGGTTCGCCAGAACGCGCTCGAACGGTGAGGATGAAAGCTGGGGGAGCAAACCGGAATAGATACCCGAGTAATCCCAACTGTAAACGATGGCAACTCGGGGATGGGTTGGCCTCCAACCAACCCCATGGCCGCAGGGAAGCCGTTTAGCTCTCCCGCCTGGGGAATACGGTCCGCAGAATTGAACCTTAAAGGAATTTGGCGGGGAACCCCCACAAGGGGGAAAACCGTGCGGTTCAATTGGAATCCACCCCCCGGAAACTTTACCCGGGCGCG
>DQ260310
GATACCCCCGGAAACTGGGGATTATACCGGATATGTGGGGCTGCCTGGAATGGTACCTCATTGAAATGCTCCCGCGCCTAAAGATGGATCTGCCGCAGAATAAGTAGTTTGCGGGGTAAATGGCCACCCAGCCAGTAATCCGTACCGGTTGTGAAAACCAGAACCCCGAGATGGAAACTGAAACAAAGGTTCAAGGCCTACCGGGCACAACAAGCGCCAAAACTCCGCCATGCGAGCCATCGCGACGGGGGAAAACCAAGTACCACTCCTAACGGGGTGGTTTTTCCGAAGTGGAAAAAGCCTCCAGGAATAAGAACCTGGGCCAGAACCGTGGCCAGCCGCCGCCGTTACACCCGCCAGCTCGAGTTGTTGGCCGGTTTTATTGGGGCCTAAAGCCGGTCCGTAGCCCGTTTTGATAAGGTCTCTCTGGTGAAATTCTACAGCTTAACCTGTGGGAATTGCTGGAGGATACTATTCAAGCTTGAAGCCGGGAGAAGCCTGGAAGTACTCCCGGGGGTAAGGGGTGAAATTCTATTATCCCCGGAAGACCAACTGGTGCCGAAGCGGTCCAGCCTGGAACCGAACTTGACCGTGAGTTACGAAAAGCCAAGGGGCGCGGACCGGAATAAAATAACCAGGGTAGTCCTGGCCGTAAACGATGTGAACTTGGTGGTGGGAATGGCTTCGAACTGCCCAATTGCCGAAAGGAAGCTGTAAATTCACCCGCCTTGGAAGTACGGTCGCAAGACTGGAACCTAAAAGGAATTGGCGGGGGGACACCACAACGCGTGGAGCCTGGCGGTTTTATTGGGATTCCACGCAGACATCTCACTCAGGGGCGACAGCAGAAATGATGGGCAGGTTGATGACCTTGCTTGACAAGCTGAAAAGGAGGTGCAT
>EF503697
TAAAATGACTAGCCTGCGAGTCACGCCGTAAGGCGTGGCATACAGGCTCAGTAACACGTAGTCAACATGCCCAAAGGACGTGGATAACCTCGGGAAACTGAGGATAAACCGCGATAGGCCAAGGTTTCTGGAATGAGCTATGGCCGAAATCTATATGGCCTTTGGATTGGACTGCGGCCGATCAGGCTGTTGGTGAGGTAATGGCCCACCAAACCTGTAACCGGTACGGGCTTTGAGAGAAGTAGCCCGGAGATGGGCACTGAGACAAGGGCCCAGGCCCTATGGGGCGCAGCAGGCGCGAAACCTCTGCAATAGGCGAAAGCCTGACAGGGTTACTCTGAGTGATGCCCGCTAAGGGTATCTTTTGGCACCTCTAAAAATGGTGCAGAATAAGGGGTGGGCAAGTCTGGTGTCAGCCGCCGCGGTAATACCAGCACCCCGAGTTGTCGGGACGATTATTGGGCCTAAAGCATCCGTAGCCTGTTCTGCAAGTCCTCCGTTAAATCCACCTGCTCAACGGATGGGCTGCGGAGGATACCGCAGAGCTAGGAGGCGGGAGAGGCAAACGGTACTCAGTGGGTAGGGGTAAAATCCATTGATCTACTGAAGACCACCAGTGGCGAAGGCGGTTTGCCAGAACGCGCTCGACGGTGAGGGATGAAAGCTGGGGGAGCAAACCGGATTAGATACCCGGGGTAGTCCCAGCTGTAAACGGATGCAGACTCGGGTGATGGGGTTGGCTTCCGGCCCAACCCCAATTGCCCCCAGGCGAAGCCCGTTAAGATCTTGCCGCCCTGTCAGATGTCAGGGCCGCCAATACTCGAAACCTTAAAAGGAAATTGGGCGCGGGAAAAGTCACCAAAAGGGGGTTGAAACCCTGCGGGTTATATATTGTAAACC
"""


if __name__ == "__main__":
    main()

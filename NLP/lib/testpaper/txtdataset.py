# import torch.utils.data as data
import os
import torch
from torchtext.data.example import Example
import torchtext.data as data
import numpy as np
import pkuseg
from utils.txt_utils import gen_question_no
import copy
from config import logger


'''
1、https://blog.csdn.net/guofei_fly/article/details/104168560 torchtext的简单使用
2、https://blog.csdn.net/qq_40367479/article/details/102772334 使用pytorch和torchtext进行文本分类
3、https://zhuanlan.zhihu.com/p/31139113 torchtext入门教程，轻松玩转文本数据处理
4、https://pytorch.org/text/ torchtext
5、https://www.jianshu.com/p/da3a5d5ed2ba
5、https://towardsdatascience.com/deep-learning-for-nlp-with-pytorch-and-torchtext-4f92d69052f
6、https://pytorch.org/text/_modules/torchtext/datasets/text_classification.html#TextClassificationDataset ！！！！！
7、https://pytorch.org/text/_modules/torchtext/data/batch.html#Batch ！！！
torchtext是一个高效、有力的文本预处理库（其对NLP的作用类似于torchvision之于CV），提供了涵盖上述诸步骤的一站式文本预
处理功能。其预处理结果不仅可用于pytorch，也可用于其他框架的使用。
'''

TAG_QUESTION = 1
TAG_CONTENT = 2
TAG_ANSWER = 3
TAG_ANSWER_AREA = 4

TARGETS = {1:'QUERSTION', 2:'CONTENT', 3:'ANSWER', 4:'ANSWER_AREA'}
STOP_WORDS = ['的','地', ',','.','，','得','(','（',')',
              '）','_','—','。','{','}','(',')','.','【','】',
              '：','；',':',']','[','｛','｝','。','}{','…………','∥{']

# 定义分词工具





# 定义停用词表
# stopwords = open('stopwords', encoding='utf-8').read().strip().split('\n')



def build_vocab(field, lexicon):
    vocab_lists = []
    lexicon = sorted(lexicon)
    vocab_lists.append(lexicon)
    field.build_vocab(vocab_lists, min_freq=1)


class TextPaperDataSet(data.Dataset):
    '''
    加载试卷内容训练数据
    '''
    def __init__(self,data_root,token, split='train', fields=None,include_unk=True, **kwargs):
        # super(TextPaperDataSet, self).__init__()
        self.data_root = data_root
        self.token = token
        self.include_unk = include_unk
        self.split = split
        self.fields = fields
        self.origin_fields = fields
        self.question_no = gen_question_no()
        self.data = self.__load_dataset__()
        super(TextPaperDataSet, self).__init__(self.data, self.fields, **kwargs)


    def __load_dataset__(self):
        logger.info('begin load data')
        data_path = os.path.sep.join([self.data_root, '{}.txt'.format(self.split)])
        examples = []
        with open(data_path, 'r', encoding='UTF-8-sig') as f:
            source = f.readlines()
        for line in source:
            d,l = line.rsplit('|',1)
            d = d.replace('（','(').replace('）',')').replace('、','.').replace('．','.').replace('、','.').strip()
            if d is not None and len(d) > 0:
                examples.append([d,l])
        return examples


    def __getitem__(self, idx):
        example = self.examples[idx].copy()
        if int(example[1]) == TAG_QUESTION:
            pku = self.question_no[np.random.randint(len(self.question_no))]
            pku = pku.replace('（','(').replace('）',')').replace('、','.').strip()
            example[0] = '{} {}'.format(pku, example[0])
        example = Example.fromlist(data=example, fields=self.origin_fields)
        example.label = int(example.label) - 1 
        return example


    def __iter__(self):
        for x in self.examples:
            example = x.copy()
            if int(example[1]) == TAG_QUESTION:
                pku = self.question_no[np.random.randint(len(self.question_no))]
                pku = pku.replace('（','(').replace('）',')').replace('、','.').strip()
                example[0] = '{} {}'.format(pku, example[0])
            example = Example.fromlist(data=example, fields=self.origin_fields)
            example.label = int(example.label) - 1 
            yield example


if __name__ == '__main__':
    import argparse
    from torchtext.data import Iterator, BucketIterator,Iterator
    from preprocess import  load_custom_dict
    parser = argparse.ArgumentParser(description='test paper dataset')
    parser.add_argument('--data_root', default='D:\\PROJECT_TW\\git\\data\\testpaper',help='data set root')
    args = parser.parse_args()

    lexicon = load_custom_dict(args.data_root)
    seg = pkuseg.pkuseg(user_dict=lexicon)    

    def tokenizer(text):    
        words = [wd for wd in seg.cut(text) if wd in lexicon]    
        new_words = []
        for x in words:
            if x not in new_words:
               new_words.append(x)
        if len(new_words) == 0:
            new_words.append('<unk>')
        return new_words 

    TEXT = data.Field(tokenize=tokenizer,lower=False, batch_first=True,include_lengths=True,fix_length=10, init_token=None)
    LABEL = data.Field(sequential=False, use_vocab=False)

    train = TextPaperDataSet(data_root=args.data_root, split='train', token=None, fields=[('text',TEXT),('label', LABEL)])
    valid = TextPaperDataSet(data_root=args.data_root, split='train', token=None, fields=[('text',TEXT),('label', LABEL)])

    # 注意因为是采用增强数据方式，所以需预先将用户字典增加到TEXT field vocab里面去
    build_vocab(TEXT, lexicon)

    print(TEXT.vocab.stoi)


    for item in train:
        print('text:', item.text, ' label:', item.label)


    train_iter,valid_iter = BucketIterator.splits(
        (train,valid),
        batch_sizes=(16,16),
        device=torch.device('cpu'),
        sort_within_batch=False,
        sort = False,
        shuffle=True,
        repeat=False)

    print(TEXT.vocab.stoi)
   
    # # for _ in range(4):
    for batch in valid_iter:
        feature, target = batch.text, batch.label     
        print('feature: ', feature[0], 'offsets:', feature[1])
        print('target:', target)
        # print('feature size:', feature.size())
    #     break;
        # break;
    # print(TEXT.vocab.stoi)
    # print('vocab len:', len(TEXT.vocab))





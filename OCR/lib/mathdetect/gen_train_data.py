from __future__ import print_function
import os
import argparse
import numpy as np
import random
from utils.pdfutils import gen_latex_pdf,gen_latex_img_pos
import shutil
import cv2

# 通过PDF，生成训练数据
def gen_train_data(data_root, text_file, formula_file, begin_idx=0,gen_size=100):
    with open(os.path.sep.join([data_root, text_file]), 'r', encoding='utf8') as f:
        texts = f.readlines()

    with open(os.path.sep.join([data_root, formula_file]),'r', encoding='utf8') as f:
        formulas =  f.readlines()

    for idx in range(begin_idx, begin_idx+gen_size):
        try:
            gen_latex_pdf(data_root=data_root, file_name=str(idx),max_phrase=15,texts=texts, latexs=formulas)
            if os.path.exists(os.path.sep.join([data_root, 'pdf', f'{idx}.log'])):
                raise Exception(f'gen {idx} image error !')
            gen_latex_img_pos(data_root=data_root, file_name=str(idx),imgH=1024)    
            if idx % 10 == 0:
                print('gen file :', idx)
            os.remove(os.path.sep.join([data_root,'pdf', f'{idx}.pdf']))
            os.remove(os.path.sep.join([data_root,'pdf', f'{idx}_color.pdf']))
        except Exception as e:
            print(e)

# 特殊单个图形，只需根据单个图形的大小生成位置信息
def gen_train_special_data(data_root, image_dir, type='m'):
    file_lists = os.listdir(os.path.sep.join([data_root, image_dir]))
    for idx, file_name in enumerate(file_lists):
        if idx % 10 == 0:
            print('生成特别训练数据：', idx)
        src_file = os.path.sep.join([data_root, image_dir, file_name])
        dest_file = os.path.sep.join([data_root, 'data', 'images','autogen',f'{type}_{idx}.png'])
        shutil.copyfile(src_file, dest_file)
        image = cv2.imread(dest_file, cv2.IMREAD_COLOR)
        height, width , _ = image.shape
        anno_dest_file = os.path.sep.join([data_root, 'data','annotations','autogen', f'{type}_{idx}.pmath' if type=='m' else f'{type}_{idx}.ppic'])
        pos = np.array([[0,0,width,height,0 if type=='m' else 1]])
        np.savetxt(anno_dest_file,pos,'%.3f', ',', )






def split(full_list,shuffle=False,ratio=0.2):
    n_total = len(full_list)
    offset = int(n_total * ratio)
    if n_total==0 or offset<1:
        return [],full_list
    if shuffle:
        random.shuffle(full_list)
    sublist_1 = full_list[offset:]
    sublist_2 = full_list[:offset]
    return sublist_1,sublist_2            

# 根据图片目录取出图片名，并保存到traing_data, valid_data两个文件中，提供给训练程序训练
def gen_train_txt(data_root, img_dir, sub_dir):
    img_path = os.path.sep.join([data_root,'data',img_dir, sub_dir])
    img_files = os.listdir(img_path)
    all_data = ['autogen/{}'.format(x.replace('.png','')) for x in img_files]
    train_data, valid_data = split(all_data, True, ratio=0.1)

    with open(os.path.sep.join([data_root,'data','training_data']),'w',encoding='utf-8') as f:
        f.writelines('\n'.join(train_data))

    with open(os.path.sep.join([data_root,'data','valid_data']),'w',encoding='utf-8') as f:
        f.writelines('\n'.join(valid_data))

    print(len(all_data))
    print(len(train_data))
    print(len(valid_data))




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='gen latex pos train data')
    parser.add_argument('--data_root', default='D:\\PROJECT_TW\\git\\data\\mathdetect',help='data set root')
    parser.add_argument('--text_file', default='knowledge.txt', type=str, help='生成PDF的文本')
    parser.add_argument('--formula_file', default='formuls.txt', type=str, help='数学公式文本')
    parser.add_argument('--gen_size', default='5',type=int,help='gen size')    
    args = parser.parse_args()
    # gen_train_data(data_root=args.data_root, 
    #                 text_file=args.text_file, 
    #                 formula_file=args.formula_file,
    #                 begin_idx=1,
    #                 gen_size=2000)
    # gen_train_txt(args.data_root, 'images', 'autogen')

    # gen_train_special_data(data_root=args.data_root,image_dir='singleformula',type='m')
    # gen_train_special_data(data_root=args.data_root,image_dir='picture',type='p')

    # gen_train_txt(args.data_root, 'images', 'autogen')

    # 暂时不用，采用tools/gen_data_from_paper.py， 生成训练数据
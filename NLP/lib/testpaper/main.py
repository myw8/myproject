# -*- coding: UTF-8 -*-
from config import _C as cfg, logger
import argparse
# from utils.docx_utils import convert_docx
from utils.html_utils import parse_html_paper
from utils.txt_utils import remove_puct
from txtdataset import TARGETS,STOP_WORDS,TAG_QUESTION,TAG_CONTENT,TAG_ANSWER,TAG_ANSWER_AREA
import os 
import shutil
from paper_detect import PaperDetect,Q_TYPE_SELECT,Q_TYPE_EMPTY,Q_TYPE_QA,Q_TYPE_UNK
import numpy as np
import json
import re
from utils.token_utils import lexer




def clean_env(data_path):
    if os.path.exists(data_path):
        shutil.rmtree(data_path)
    if not os.path.exists(data_path):
        os.mkdir(data_path)    


class PaperQuestion(object):
    def __init__(self, qid, parent_qid, question_no, question_level, question_type):
        # 问题索引号
        self.qid = qid
        # 父问题索引号
        self.parent_qid = parent_qid
        self.question_no = remove_puct(question_no)
        self.question_level = question_level
        # 子问题数
        self.sub_question_count = 0
        # 对应问题位置区域, 位置区域包含子问题
        self.postion = [-1,-1]
        # 问题类型   1: 选择题  2: 填空题  3: 问答题
        self.question_type = question_type
        # 问题内容
        self.content = ''
        # 答案
        self.answer = ''

        self.answer_content = ''
        # 原始答案
        self.resolve = ''

    def to_map(self):
        qmap = {'question':{
            'qid':self.qid,
            'pqid':self.parent_qid,
            'qno':self.question_no,
            'qlevel':self.question_level,
            'position':self.postion,
            'sub_q_count':self.sub_question_count,
            'qtype':self.question_type,
            'content':self.content,
            'answer':self.answer,
            'ans_content':self.answer_content
        }}
        return qmap

    def __repr__(self):
        return json.dumps(self.to_map(),ensure_ascii=False)

    def __str__(self):
        return json.dumps(self.to_map(),ensure_ascii=False)


class TestPaperParse(object):
    def __init__(self, paper_detect):
        self.pdetect = paper_detect
        self.question_lists = None
        self.line_detect_map = None
        self.answer_areas_lists = None
        self.origin_paper_lines = None
        self.lexer = lexer()

    # 将doc文件进行转换，转换成HTML，再对HTML内容进行解析
    # def paper_doc_convert(self, file_name):
    #     clean_env(cfg.paper.temp_path)
    #     logger.info('开始处理 %s,  转换成HTML' % os.path.sep.join([cfg.paper.data_root,file_name]))
    #     convert_docx(cfg.server.libreoffice, os.path.sep.join([cfg.paper.data_root,file_name]), cfg.paper.temp_path)
    #     logger.info('转换成HTML，开始解析试卷HTML内容')
    #     pcontent, pimage = parse_html_paper(os.path.sep.join([cfg.paper.temp_path, '%s.html' % file_name.rsplit('.',1)[0]]))
    #     logger.debug('解析后的HTML内容：%s' % '\n'.join(pcontent))
    #     return pcontent, pimage

    def detect_by_idx(self, idx):
        return self.line_detect_lists[idx]

    def __get_detect_type_lists__(self, lines):
        self.line_detect_lists = [self.pdetect.detect(x.strip()) for x in lines]

        # 答案开始标记
        ans_start_flags = []

        # 标记问题开始
        cur_question_level = None
        cur_question_id = None

        # 该问题级别下的问题ID号
        qus_level_ids = {}

        # 修改部分检测的文本类型，主要是针对解答部分的子问题错误
        for idx, _ in enumerate(self.line_detect_lists):
            ltype, (qlevel, l_id) = self.line_detect_lists[idx]

            if ltype == TAG_QUESTION:
                if qlevel in ans_start_flags:
                    # 本次问题级别已开始问题答案
                    # 检测本级别问题是否有相同题号，如存在相同题号，则表明该问题应为上一问题答案
                    if l_id in qus_level_ids[qlevel]:
                        self.line_detect_lists[idx] = [TAG_ANSWER, (None,None)]

                # 问题已发生变化，到新级别问题, 清理缓存
                if qlevel != cur_question_level:
                    if cur_question_level in ans_start_flags:
                        del ans_start_flags[ans_start_flags.index(cur_question_level)]

                    if cur_question_level in qus_level_ids:
                        del qus_level_ids[cur_question_level]

                cur_question_level = qlevel
                cur_question_id = l_id
                if qlevel not in qus_level_ids:
                    qus_level_ids[qlevel] = [l_id]
                else:
                    qus_level_ids[qlevel].append(l_id)

            elif ltype == TAG_ANSWER:
                if  cur_question_level not in ans_start_flags:
                    ans_start_flags.append(cur_question_level)


    def __get__detect_type_lists_2__(self, lines):
        self.line_detect_lists = [self.pdetect.detect(x.strip()) for x in lines]
        answer_start_flag = False
        answer_question_levels = []
        answer_question_ids = []

        for idx, _ in enumerate(self.line_detect_lists):
            ltype, (qlevel, l_id) = self.line_detect_lists[idx]
            if answer_start_flag:
                if ltype == TAG_QUESTION:
                    if l_id in answer_question_ids:
                        self.line_detect_lists[idx] = [TAG_ANSWER, (None,None)]
                    else:
                        if qlevel in answer_question_levels:
                            answer_start_flag = False
                            answer_question_levels = answer_question_levels[0:answer_question_levels.index(qlevel)+1]
                            answer_question_ids = [l_id]
                        else:
                            self.line_detect_lists[idx] = [TAG_ANSWER, (None,None)]
            else:
                if ltype == TAG_QUESTION:
                    if qlevel not in answer_question_levels:
                        answer_question_levels.append(qlevel)
                    answer_question_ids.append(l_id)
                elif ltype == TAG_ANSWER:
                    answer_start_flag = True



    # 将试卷内容进行分隔，分隔成问题区域、参考答案区域， 并去掉一些无用的行
    def paper_split_content(self,lines):
        lines = [x.strip() for x in lines]

        self.origin_paper_lines = lines
        self.__get__detect_type_lists_2__(lines)

        line_detect_lists = np.array([self.detect_by_idx(lidx)[0] for lidx, x in enumerate(lines)])
        q_lines = None
        answer_lines = None
        q_ans_area_pos = np.where(line_detect_lists == TAG_ANSWER_AREA)[0]
        if len(q_ans_area_pos) > 0:
            q_lines = lines[0:q_ans_area_pos[0]]
            answer_lines = lines[q_ans_area_pos[0]:]
        else:
            q_lines = lines

        # 分解试题
        self.question_lists = self.paper_split_question(lines=q_lines)

        # 组合试题区域自带答案
        self.merge_question_content(lines=lines)


        # 参考答案区域答案处理
        if answer_lines is not None and len(answer_lines) > 0:
            self.answer_areas_lists  = self.paper_split_answer_area_2(answer_lines)
    
    def paper_split_answer_area_2(self, answer_lines):
        # 标记答案开始标记
        answer_start_level = []
        answer_cur_idx = None
        for aidx,aline in enumerate(answer_lines):
            # 将行里面带的答案的字去掉

            dline = aline.replace('解','').replace('答','').replace('命题','')
            ltype, (qlevel, l_id) = self.pdetect.detect(aline)

            if ltype == TAG_QUESTION:

                
                result = self.__find_question_by_level__(question_level=qlevel, question_no=l_id, has_no_answer=True)

                # print('......................................................')
                # print('text:', aline)
                # print('result:', result)
                # print('......................................................')

                # 检测是否是新题答案， 检测当前级别与检测的级别、或检测级别的当级级别是否相同
                # 这里采用了简化的方式，选择不是第一级目录的问题
                if result is not None:
                    if qlevel in answer_start_level:
                        del answer_start_level[answer_start_level.index(qlevel)]
                        answer_cur_idx = None

                    if qlevel not in answer_start_level:
                        _qidx,  _question = result
                        answer_start_level.append(qlevel)
                        answer_cur_idx = _qidx

                    if answer_cur_idx is not None:
                        self.question_lists[answer_cur_idx].answer_content = '{}\n{}'.format(self.question_lists[answer_cur_idx].answer_content, aline)


            else:
                if answer_cur_idx is not None:
                    self.question_lists[answer_cur_idx].answer_content = '{}\n{}'.format(self.question_lists[answer_cur_idx].answer_content, aline)





    # 参考答案区域解析、划分
    def paper_split_answer_area(self, answer_lines):
        # print('answer lines:', answer_lines)
        '''
        处理流程：
        1、从question list找到大题（选择题、填空题、。。。）的类型
        2、分解answer_lines，分隔成大题区域
        3、针对大题，对大题里的内容用正则方式进行分隔（采用不同方式），再设置到question里对应的题目上面
        '''
        _area_select = []
        _area_empty = []
        _area_qa = []

        _area_flag = None

        for aidx,aline in enumerate(answer_lines):
            ltype, (qlevel, l_id) = self.pdetect.detect(aline)
            if ltype == TAG_QUESTION:
                qtype = self.pdetect.detect_question_type(aline)
                if qtype != Q_TYPE_UNK:
                    _area_flag = qtype

            if _area_flag == Q_TYPE_SELECT:
                _area_select.append(aline)
            elif _area_flag == Q_TYPE_EMPTY:
                _area_empty.append(aline)
            elif _area_flag == Q_TYPE_QA:
                _area_qa.append(aline)

        if _area_select:
            self.__merge_answer_select__(_area_select)

        if _area_empty:
            self.__merge_answer_empty__(_area_empty)

        if _area_qa:
            self.__merge_anser_qa__(_area_qa)

    def __find_question_by_no__(self,parent_id, question_type,question_no=None):
        if question_no is not None:
            question_no = remove_puct(question_no)
            qlists = [(idx,x) for idx, x in enumerate(self.question_lists) if (x.question_type==question_type and 
                                                                    x.question_no==question_no and x.parent_qid==parent_id)]
        else:
            qlists = [(idx,x) for idx, x in enumerate(self.question_lists) if (x.question_type==question_type and x.parent_qid==parent_id)]

        if len(qlists) == 0:
            return None

        if question_no is None:
            return qlists
        else:
            if len(qlists) > 1:
                return None
            else:
                return qlists[0]

    def __find_question_by_level__(self, question_level, question_no, has_no_answer=False):
        question_no = remove_puct(question_no)
        if has_no_answer:
            qlists = [(idx, x) for idx,x in enumerate(self.question_lists) if x.question_no == question_no 
                                                                    and x.question_level == question_level
                                                                    and x.parent_qid != 0
                                                                    and len(x.answer_content) == 0]
        else:
            qlists = [(idx, x) for idx,x in enumerate(self.question_lists) if x.question_no == question_no 
                                                                    and x.parent_qid != 0
                                                                    and x.question_level == question_level]

        if len(qlists) == 0:
            return None

        return qlists[0]

    def __lexer_token__(self, text):
        lexer = self.lexer.clone()
        lexer.input(text)
        tok_lists = []
        while True:
            tok = lexer.token()
            if not tok:
                break;
            tok_lists.append(tok)
        return tok_lists

    # 参考答案区域填选择题将值设置到问题答案区
    def __merge_answer_select__(self, alines):
        alines = [x.strip() for x in alines]
        answer_lines = []
        for line in alines[1:]:
            tok_lists = self.__lexer_token__(line)
            tok_pos = [x.lexpos for x in tok_lists]
            tok_pos.append(len(line))
            tok_pos = list(zip(tok_pos[0:-1], tok_pos[1:]))
            answer_lines.extend([(tok_lists[idx].value, tok_lists[idx].type, line[x[0]:x[1]]) for idx, x in enumerate(tok_pos)])

        ltype, (qlevel, l_id) = self.pdetect.detect(alines[0])

        result = self.__find_question_by_no__(parent_id=0, question_type=Q_TYPE_SELECT,question_no=l_id)
        if result is None:
            return
        p_qidx, p_question = result


        for item in answer_lines:
            val, atype, content = item
            
            if atype in ['SegNumOne','SegNumTwo']:
                # 标准的题号  1. 1)
                result = self.__find_question_by_no__(parent_id=p_question.qid,
                                                        question_type=Q_TYPE_SELECT,
                                                        question_no=val)
                if result is not None:
                    qidx, _ = result
                    self.question_lists[qidx].answer_content = content
                    self.question_lists[qidx].answer = content.replace(val,'').strip()
            elif atype == 'SegNumSpec':
                # 特殊的题号  1--4
                bidx, eidx = re.findall('\d+',val)
                a_idx_lists = list(range(int(bidx), int(eidx)+1))
                a_idx_lists = [str(x) for x in a_idx_lists]
                for idx, v in enumerate(re.findall(r'[A-Za-z]', content)):
                    result = self.__find_question_by_no__(parent_id=p_question.qid,
                                                            question_type=Q_TYPE_SELECT,
                                                            question_no=a_idx_lists[idx])
                    if result is not None:
                        qidx, _ = result
                        self.question_lists[qidx].answer_content = v
                        self.question_lists[qidx].answer = v       





    # 参考答案区域填空题将值设置到问题答案区
    def __merge_answer_empty__(self, alines):
        # print('填空题：', alines)
        alines = [x.strip() for x in alines]
        answer_lines = []
        for line in alines[1:]:
            tok_lists = self.__lexer_token__(line)
            tok_pos = [x.lexpos for x in tok_lists]
            tok_pos.append(len(line))
            tok_pos = list(zip(tok_pos[0:-1], tok_pos[1:]))
            answer_lines.extend([(tok_lists[idx].value, tok_lists[idx].type, line[x[0]:x[1]]) for idx, x in enumerate(tok_pos)])

        ltype, (qlevel, l_id) = self.pdetect.detect(alines[0])
        result = self.__find_question_by_no__(parent_id=0, question_type=Q_TYPE_EMPTY,question_no=l_id)
        if result is None:
            return
        p_qidx, p_question = result

        for item in answer_lines:
            val, atype, content = item
            # print('token:',atype , val, ':', content)

            if atype in ['SegNumOne','SegNumTwo']:
                result = self.__find_question_by_no__(parent_id=p_question.qid,
                                                        question_type=Q_TYPE_EMPTY,
                                                        question_no=val)
                if result is not None:
                    qidx, _ = result
                    self.question_lists[qidx].answer_content = content
                    self.question_lists[qidx].answer = content.replace(val,'').strip()
            elif atype == 'SegNumSpec':
                pass
        

    # 参考答案区域问答题将值设置到问题答案区, 问题只处理大题
    def __merge_anser_qa__(self, alines):
        # qlists = [x for x in self.question_lists if (x.parent_qid==0 and x.question_type==Q_TYPE_QA)]
        # print('qlists:', qlists)
        # qa_level = None
        
        ltype, (qlevel, l_id) = self.pdetect.detect(alines[0])
        p_qidx, p_question = self.__find_question_by_no__(parent_id=0, question_type=Q_TYPE_QA, question_no=l_id)

        # print('主问题：', p_question)

        cur_qidx = None
        cur_question = None

        for aline in alines[1:]:
            ltype, (qlevel, l_id) = self.pdetect.detect(aline)
            if ltype == TAG_QUESTION:
                result = self.__find_question_by_no__(parent_id=p_question.qid,
                                                                      question_type=Q_TYPE_QA,
                                                                      question_no=l_id)
                if result is not None:
                    cur_qidx, cur_question = result

            if cur_qidx != None:
                self.question_lists[cur_qidx].answer_content = '{}\n{}'.format(self.question_lists[cur_qidx].answer_content,aline)


                    


    # 将试卷问题区域划分
    def paper_split_question(self, lines,parent_id=0,begin_idx=0,parent_question_type=-1, parent_question_level='TOP', answer_start_flag=False):
        '''
        处理流程：
        1、检测 line 类型 （问题、答案、解析、内容、答案区域开始, 备注）
        2、提取分词, 对第一个分词进行问题级别分类，根据当前问题级别对该行进行问题分级
        3、到第一步

        保存结构：
        Question:
            id:  ID号
            parent_id: 上级ID号
            content: 问题内容  (后期再进行分解成答案、问题等部分)
        '''
        # print('paper split content ....', lines)
        lines = [x.strip() for x in lines]

        qlists = []
        q_start_flag = False
        q_start_idx = None
        q_ans_start_flag = answer_start_flag
        q_end_idx = None
        current_level = None
        question = None
        question_id = 0



        for idx, line in enumerate(lines):
            # 检测当前行的类型
            ltype, (qlevel, l_id) = self.detect_by_idx(idx+begin_idx)
            # 对回答区进行处理， 处理回答区中题号问题

            if ltype == TAG_QUESTION:
                question_type = parent_question_type if parent_question_type != -1 else self.pdetect.detect_question_type(line)
                # 类型标记为问题
                if not q_start_flag:
                    current_level = qlevel
                    q_start_flag = True
                    q_start_idx = idx
                    question_id = question_id + 1
                    question = PaperQuestion(qid=f'{parent_id}_{question_id}', parent_qid=parent_id, 
                                             question_no=l_id, question_level=qlevel, question_type=question_type)

                else:
                    if current_level == qlevel:
                        q_end_idx = idx
                        question.postion = [q_start_idx+begin_idx, q_end_idx+begin_idx]
                        qlists.append(question)


                        if q_end_idx - q_start_idx > 1:
                            sub_qlists = self.paper_split_question(lines[q_start_idx+1:q_end_idx], 
                                                                  parent_id=question.qid, 
                                                                  begin_idx=begin_idx+q_start_idx+1, 
                                                                  parent_question_type=question.question_type,
                                                                  parent_question_level=current_level,
                                                                  answer_start_flag=q_ans_start_flag
                                                                  )
                            if len(sub_qlists) > 0:
                                qlists.extend(sub_qlists)

                        q_start_idx = idx
                        question_id = question_id + 1
                        question = PaperQuestion(qid=f'{parent_id}_{question_id}', parent_qid=parent_id, 
                                                 question_no=l_id, question_level=qlevel,question_type=question_type)


        if question is not None:
            q_end_idx = len(lines)
            question.postion = [q_start_idx+begin_idx, q_end_idx+begin_idx]
            qlists.append(question)
            if q_end_idx - q_start_idx > 1:
                sub_qlists = self.paper_split_question(lines[q_start_idx+1:q_end_idx], 
                                                      parent_id=question.qid, 
                                                      begin_idx=begin_idx+q_start_idx+1,
                                                      parent_question_type=question.question_type,
                                                      parent_question_level=current_level,
                                                      answer_start_flag=q_ans_start_flag)
                if len(sub_qlists) > 0:
                    qlists.extend(sub_qlists)

        return qlists


    def __get_child_question__(self,parent_id):
        qlists = [x for x in self.question_lists if x.parent_qid == parent_id]
        return qlists, q_end_position


    # 问题区域内容填充, 注意这里前提是问题是按顺序排列
    def merge_question_content(self,lines, question_id=0):
        qlists = [x for x in self.question_lists if x.parent_qid == question_id]

        if question_id != 0:
            qidx = [idx for idx, x in enumerate(self.question_lists) if x.qid == question_id][0]
            # 该问题范围
            qcp = self.question_lists[qidx].postion

            # 填充该问题子问题个数
            self.question_lists[qidx].sub_question_count = len(qlists)

            if len(qlists) > 0:
                qcp[1] = qlists[0].postion[0]

            answer_lines = []
            answer_start_flag = False
            cur_answer_question_level = None
            for lidx, line in enumerate(lines[qcp[0]:qcp[1]]):
                ltype, (qlevel, l_id) = self.detect_by_idx(lidx + qcp[0])

                if not answer_start_flag:
                    if ltype == TAG_QUESTION or ltype == TAG_CONTENT:
                        self.question_lists[qidx].content = '{}{}\n'.format(self.question_lists[qidx].content, line)
                        # cur_answer_question_level = qlevel

                    elif ltype == TAG_ANSWER:
                        # 注意后期需要修改，防止换行的情况
                        if self.question_lists[qidx].question_type == Q_TYPE_SELECT  and line.find('答案') != -1:
                            self.question_lists[qidx].answer = ''.join(re.findall(r'[A-Za-z]|\d',line))      
                        answer_lines.append(line)
                        answer_start_flag = True
                else:
                    if ltype == TAG_QUESTION:
                        # if qlevel == cur
                        self.question_lists[qidx].content = '{}{}\n'.format(self.question_lists[qidx].content, line)
                        answer_start_flag = False
                        # answer_lines.append(line)
                    elif ltype == TAG_CONTENT:
                        answer_lines.append(line)
                        # question_lists[qidx].answer_content = '{}{}\n'.format(question_lists[qidx].answer_content, line)
                    elif ltype == TAG_ANSWER:
                        # 注意后期需要修改，防止换行的情况
                        if self.question_lists[qidx].question_type == Q_TYPE_SELECT  and line.find('答案') != -1:
                            self.question_lists[qidx].answer = ''.join(re.findall(r'[A-Za-z]|\d',line))      

                        # question_lists[qidx].answer_content = '{}{}\n'.format(question_lists[qidx].answer_content, line)
                        answer_lines.append(line)

            self.question_lists[qidx].answer_content = '\n'.join(answer_lines)

        for qitem in qlists:
            self.merge_question_content(lines,question_id=qitem.qid)
                

    # 检测问题连续性
    def check_question_no_continues(self, question_id=0):
        qmap = {}
        qlists = [x for x in self.question_lists if x.parent_qid == question_id]
        if len(qlists) > 0:
            if question_id != 0:
                question_no = [x for x in self.question_lists if x.qid == question_id][0].question_no
            else:
                question_no = str(question_id)
            q_no_lists = [x.question_no for x in qlists]
            q_no_level = qlists[0].question_level
            q_no_loss = self.pdetect.detect_loss_question(q_no_lists, q_no_level)
            qmap[question_no] = {'q_no_lists':q_no_lists, 'q_no_level':q_no_level, 'q_no_loss':q_no_loss}
            
            for qitem in qlists:
                outmap = self.check_question_no_continues(question_id=qitem.qid)
                qmap.update(outmap)

        return qmap

    # 检测问题是否都有答案
    def check_empty_question_answer(self):
        pass


    # 调整试题答案位置，主要针对填空题、问答题， 某些大题的子题有答案，但其它子题没有答案，将答案上移到大题上面
    def adjust_question_answer(self, question_id=0):
        # 问题不是选择题
        qlists = [x for x in self.question_lists if x.parent_qid == question_id and x.question_type != Q_TYPE_SELECT]

        if question_id != 0:
            qidx = [idx for idx, x in enumerate(self.question_lists) if x.qid == question_id][0]
            q = self.question_lists[qidx]
            has_sub_questions = any([x.sub_question_count > 0 for x in qlists])

            if has_sub_questions:
                for item in qlists:
                    self.adjust_question_answer(question_id=item.qid)

            else:
                # 检测问题是否已是最底层问题,并且带有答案
                if q.sub_question_count == 0 and len(q.answer_content) > 0:
                    # 检测同级问题是否有子问题
                    has_sub_questions =  [x.sub_question_count for x in self.question_lists if x.parent_qid == q.parent_qid]
                    if sum(has_sub_questions) == 0:

                        # 取得同级所有问题，检测是否有答案
                        has_answer =  [len(x.answer_content)>0 for x in self.question_lists if x.parent_qid == q.parent_qid]
                        
                        # 如果没有答案数 >= 有答案数，则将子答案合并并设置到上一极问题的答案域里面
                        if has_answer.count(False) >= has_answer.count(True):
                            p_qid = [idx for idx, x in enumerate(self.question_lists) if x.qid == q.parent_qid][0]
                            sub_q_ids = [idx for idx, x in enumerate(self.question_lists) if x.parent_qid == q.parent_qid]
                            sub_q_ans = ''
                            for idx in sub_q_ids:
                                sub_q_ans = ''.join([sub_q_ans,self.question_lists[idx].answer_content])
                                self.question_lists[idx].answer_content = ''

                            self.question_lists[p_qid].answer_content = ''.join([self.question_lists[p_qid].answer_content, sub_q_ans])

        for qitem in qlists:
            self.adjust_question_answer(question_id=qitem.qid)            

    def adjust_question_answer_2(self,question_id=0):
        # 问题不是选择题
        qlists = [(idx,x) for idx, x in enumerate(self.question_lists) if x.parent_qid == question_id and x.question_type != Q_TYPE_SELECT]
        if question_id != 0 and len(qlists) > 0:
            l_qidx, l_question = [(idx, x) for idx , x in enumerate(self.question_lists) if x.qid == question_id][0]

            
            # 查找该问题是否包括子问题, 且子问题已无更下一级问题
            s_qlists = [x[1] for x in qlists if x[1].sub_question_count > 0]
            if len(s_qlists) > 0:
                for item in s_qlists:
                    self.adjust_question_answer_2(item.qid)
            else:
                # 本级问题不能是标题性质的问题（这里特指父标题为0，和 内容里面包括选做题，必做题）。如：一、填空题
                if l_question.parent_qid != 0: 
                    if l_question.content.find('选做题') == -1 and l_question.content.find('必做题') == -1:
                        for _idx, _question in qlists:
                            self.question_lists[l_qidx].answer_content = '{}\n{}'.format(self.question_lists[l_qidx].answer_content, 
                                                                                         _question.answer_content)
                            self.question_lists[_idx].answer_content = ''


        for _qidx, _question in qlists:
            self.adjust_question_answer_2(_question.qid)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="试卷导入功能")
    parser.add_argument("--config_file", default="bootstrap.yml", help="配置文件路径", type=str)
    parser.add_argument("--file_name", default=u"数学答案-期中考试答案.txt", help="配置文件路径", type=str)
    parser.add_argument("--data_root", default="D:\\PROJECT_TW\\git\\data\\testpaper", help="配置文件路径", type=str)
    args = parser.parse_args()
    cfg.merge_from_file(args.config_file)    

    
    

    pdetect = PaperDetect()
    paper = TestPaperParse(pdetect)
    # pcontents, pimage = paper.paper_doc_convert(args.file_name)
    # pdetect.detect('1.本试卷分{img:2}第Ⅰ卷（选择题）和第Ⅱ卷（非选择题）两部分。第Ⅰ卷1至3页，第Ⅱ卷3至5页。')
    # pdetect.detect('2.答题前，考生务必将自己的姓名、准考证号填写在本试题相应的位置。')
    # pdetect.detect('4.考试结束后，将本试题和答题卡一并交回。')
    # pdetect.detect('【答案】{img:130}')
    # pdetect.detect('[OL]{img:149}（13）设二项式{img:150}的展开式中{img:151}的系数为A,常数项为B，若B=4A，则a的值是。')
    # pdetect.detect('【点评】三角函数与解三角形的综合性问题，是近')
    # pdetect.detect('【解】（Ⅰ）因为{img:424}的坐标为{img:425}，则{img:426}')
    # pdetect.detect('长郡中学2017—2018学年度高一第一学期第二次模块检测')
    # pdetect.detect('【试题分析】（I）分别对和两种情况讨论')
    # pdetect.detect('3．【】：A、量取液体时，视线与液体的凹液面最低处保持水平，图中俯视刻度，操作错误')
    # pdetect.detect('四、（本大题共2小题，每空2分，共18分）')
    # pdetect.detect('21．（5分）如图所示，“﹣”表示相连的两物质')
    # pdetect.detect('于是她用如图所的装置来制取CO2并验证其与Na2O2的反应。')
    # pdetect.detect('参考答案与试题解析')
    # pdetect.detect('【试题分析】（I）分别对{img:218}和{img:219}两种情况讨论{img:220}，进而可得使得等式{img:221}成立的{img:222}的取值范围；（II）（i）先求函数{img:223}，{img:224}的最小值，再根据{img:225}的定义可得{img:226}的最小值{img:227}；（ii）分别对{img:228}和{img:229}两种情况讨论{img:230}的最大值，进而可得{img:231}在区间{img:232}上的最大值{img:233}．')
    # pdetect.detect('①曲线C过坐标原点')
    # pdetect.detect('②曲线C关于坐标原点对称')
    # pdetect.detect('③若点P在曲线C上')
    # pdetect.detect('答案与解析')
    # pdetect.detect('2011年普通高等学校招生全国统一考试（安徽卷）数学（文科）答案与解析')
    # pdetect.detect('2.本部分共12小题，每小题5分，共60分。')
    # pdetect.detect('{img:157}的展开式中{img:158}的系数为.(用数字填写答案)')
    # pdetect.detect('答案：C')
    # pdetect.detect('3、{img:17}，{img:18}，{img:19}是空间三条不同的直线，则下列命题正确的是')
    # pdetect.detect('解：（Ⅰ）由已知，{img:230}')
    # pdetect.detect('解析：（1）因为满足')
    # pdetect.detect('{img:6}(1) 你所观察到的现象是什么?')
    pdetect.detect('二、解答题 （本大题共6小题，共90分.请在 答题卡制定区域内作答，解答时应写出文字说明、证明过程或演算步骤.） [来源:学*科*网]"}')
    pdetect.detect('【答案】（1）{img:277}．（2）{img:278}.\n')

    with open(os.path.sep.join([args.data_root,'output', args.file_name]), 'r', encoding='utf-8') as f:
        lines = f.readlines()


    paper.paper_split_content(lines)
    # print('\n--------------------------------\n'.join([str(x) for x in paper.question_lists]))

    # 
    paper.adjust_question_answer_2()
    print('\n--------------------------------\n'.join([str(x) for x in paper.question_lists]))


    # qmaps = paper.check_question_no_continues(qlists)
    # print(qmaps)
    






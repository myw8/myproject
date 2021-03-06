# config.py
import os.path

# gets home dir cross platform
# 关于default box min size  and max size 可参看 https://www.icode9.com/content-1-641141.html
# 关于default box https://arxiv.org/pdf/1512.02325.pdf 
HOME = os.path.expanduser("~")

# for making bounding boxes pretty
COLORS = ((255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128),
          (0, 255, 255, 128), (255, 0, 255, 128), (255, 255, 0, 128))

MEANS = (246, 246, 246)

exp_cfg = {

    'gtdb': {
        'num_classes': 2,
        'lr_steps': (80000, 100000, 120000),
        'channel':3,
        'max_iter': 120000,
        'feature_maps': [64, 32, 16, 8, 4, 2, 1],
        'min_dim': 512,
        'steps': [8, 16, 32, 64, 128, 256, 512],
        'min_sizes': [8.00, 76.8, 153.6, 230.4, 307.2, 384.0, 460.8],
        'max_sizes': [76.8, 153.6, 230.4, 307.2, 384.0, 460.8, 537.6],
        'aspect_ratios': [[2, 3, 5], [2, 3, 5, 7], [2, 3, 5, 7], [2, 3], [2, 3], [2], [2]],

        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'GTDB',

        'is_vertical_prior_boxes_enabled': True,

        'mbox': {
            '512': [8, 10, 10, 6, 6, 4, 4],
            #'512': [5, 6, 6, 4, 4, 3, 3],
            '300': [8, 10, 10, 6, 4, 4],  # number of boxes per feature map location
        },
        'extras': {
            '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256],
            '300': [256, 'S', 512, 128, 'S', 256, 128, 256, 128, 256],
        }
    },

    'math_gtdb_512': {
        'num_classes': 3,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 240000,
        'feature_maps': [64, 32, 16, 8, 4, 2, 1],
        'min_dim': 512,
        'steps': [8, 16, 32, 64, 128, 256, 512],
        'min_sizes': [8.00, 76.8, 153.6, 230.4, 307.2, 384.0, 460.8],
        'max_sizes': [76.8, 153.6, 230.4, 307.2, 384.0, 460.8, 537.6],
        'aspect_ratios': [[2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10],
                          [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'math_gtdb_512',
        'is_vertical_prior_boxes_enabled': True,
        'mbox': {
            '512': [12,12,12,12,12,12,12],
        },
        'extras': {
            '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256],
        }
    },

    'ssd300': {
        'num_classes': 2,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 132000,
        'feature_maps': [38, 19, 10, 5, 3, 1],
        'min_dim': 300,
        'steps': [8, 16, 32, 64, 100, 300],
        'min_sizes': [30, 60, 111, 162, 213, 264],
        'max_sizes': [60, 111, 162, 213, 264, 315],
        # 'min_sizes': [10, 20, 40, 60, 80, ],
        # 'max_sizes': [20, 40, 60, 80, 100, 315],

        'aspect_ratios': [[2], [2, 3], [2, 3], [2, 3], [2], [2]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'ssd300',
        'is_vertical_prior_boxes_enabled': True,
        'mbox': {
            '300': [4, 6, 6, 6, 4, 4],  # number of boxes per feature map location
        },
        'extras': {
            '300': [256, 'S', 512, 128, 'S', 256, 128, 256, 128, 256],
        }
    },


    'ssd100': {
        'num_classes': 2,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 132000,
        'feature_maps': [13, 6, 3, 2, 1],
        'min_dim': 100,
        'steps': [8, 16, 32, 50, 100],
        'min_sizes': [8, 24, 40, 57, 73],
        'max_sizes': [24,40, 57, 73, 95],
        'aspect_ratios': [[2,3,5], [2, 3, 5], [2, 3, 5], [2, 3, 5], [2,3,5], [2,3,5]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'ssd100',
        'is_vertical_prior_boxes_enabled': True,
        'mbox': {
            '100': [8, 8, 8, 8, 8, 8],  # number of boxes per feature map location
        },
        'extras': {
            '100': [256, 'S', 512, 128, 'S', 256, 128,'S', 256],
        }
    },



    'ssd512': {
        'num_classes': 2,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 132000,
        'feature_maps': [64, 32, 16, 8, 4, 2, 1],
        'min_dim': 512,
        'steps': [8, 16, 32, 64, 128, 256, 512],
        'min_sizes': [35.84, 76.8, 153.6, 230.4, 307.2, 384.0, 460.8],
        'max_sizes': [76.8, 153.6, 230.4, 307.2, 384.0, 460.8, 537.6],
        'aspect_ratios': [[2], [2, 3], [2, 3], [2, 3], [2,3], [2], [2]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'ssd512',
        'is_vertical_prior_boxes_enabled': True,
        'mbox': {
            '512': [4,6,6,6,6,4,4],
        },
        'extras': {
            '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256],
        }
    },

    'aspect512': {
        'num_classes': 2,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 132000,
        'feature_maps': [64, 32, 16, 8, 4, 2, 1],
        'min_dim': 512,
        'steps': [8, 16, 32, 64, 128, 256, 512],
        'min_sizes': [35.84, 76.8, 153.6, 230.4, 307.2, 384.0, 460.8],
        'max_sizes': [76.8, 153.6, 230.4, 307.2, 384.0, 460.8, 537.6],
        'aspect_ratios': [[2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10],
                          [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'ssd512',
        'is_vertical_prior_boxes_enabled': True,
        'mbox': {
            '512': [12,12,12,12,12,12,12],
        },
        'extras': {
            '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256],
        }
    },


    'hboxes512': {
        'num_classes': 2,
        'channel':3,
        'lr_steps': (80000, 100000, 120000),
        'max_iter': 132000,
        'feature_maps': [64, 32, 16, 8, 4, 2, 1],
        'min_dim': 512,
        'steps': [8, 16, 32, 64, 128, 256, 512],
        'min_sizes': [35.84, 76.8, 153.6, 230.4, 307.2, 384.0, 460.8],
        'max_sizes': [76.8, 153.6, 230.4, 307.2, 384.0, 460.8, 537.6],
        'aspect_ratios': [[2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10],
                          [2, 3, 5, 7, 10], [2, 3, 5, 7, 10], [2, 3, 5, 7, 10]],
        'variance': [0.1, 0.2], # variance
        'clip': True,
        'name': 'ssd512',
        'is_vertical_prior_boxes_enabled': False,
        'mbox': {
            '512': [7,7,7,7,7,7,7],
        },
        'extras': {
            '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256],
        }
    },

}
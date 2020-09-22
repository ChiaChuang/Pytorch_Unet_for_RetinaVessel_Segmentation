# PyTorch Unet Implementation for Segmentation of Retina Vessel on DRIVE dataset

This repo is a simple and easy to follow pyTorch implementation of U-net for retina vessel segmentation. 

Reference for U-net: [U-Net: Convolutional Networks for Biomedical Image Segmentation](http://arxiv.org/abs/1505.04597)

Reference for DRIVE dataset and introduction: [DRIVE: Digital Retinal Images for Vessel Extraction](https://drive.grand-challenge.org/)


## Dataset Overview

![channels_drive](https://github.com/jzsherlock4869/PyTorch_Unet_for_RetinaVessel_Segmentation/blob/master/repo_pics/channels_drive.png "RGB channels for a sample image in DRIVE")

![mask_label_drive](https://github.com/jzsherlock4869/PyTorch_Unet_for_RetinaVessel_Segmentation/blob/master/repo_pics/mask_label_drive.png "a. Original Image; b. Mask; c. Mannual Label")

```
tree -d DRIVE/
DRIVE/
├── test
│   ├── 1st_manual
│   ├── 2nd_manual
│   ├── images
│   └── mask
└── training
    ├── 1st_manual
    ├── images
    └── mask
```

## Preparation

The versions of packages used in the experiment are as follows:

```
torch == 1.5.1 

PIL == 5.4.1 

numpy == 1.16.2 

matplotlib == 3.0.3
```

## Training and Testing on DRIVE dataset



## Preliminary Results

Prediction after 160 epoches on train set.



## To Do List



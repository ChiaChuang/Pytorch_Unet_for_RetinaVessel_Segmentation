import os
import torch
import numpy as np
from glob import glob
from torch.utils.data import Dataset
from PIL import Image
import h5py
import itertools
from torch.utils.data.sampler import Sampler

from data_loader import load_dataset

class Drive(Dataset):
    """ Drive Dataset """
    def __init__(self, base_dir=None, split='train', num=None, transform=None):
        
        self.transform = transform

        self.image_list, self.label_list, self.mask_list = load_dataset(rel_path=base_dir)
        
        shuffle_ids = np.random.permutation(len(self.image_list))
        self.image_list = self.image_list[shuffle_ids, :, :, :]
        self.label_list = self.label_list[shuffle_ids, :, :, :]
        self.mask_list = self.mask_list[shuffle_ids, :, :, :]

    def __len__(self):
        return len(self.image_list)

    def __getitem__(self, idx):
        sample = self.image_list[idx]
        
        sample = {
            'image': self.image_list[idx, :, :, :], 
            'label': self.label_list[idx, 0:1, :, :]}
        if self.transform:
            sample = self.transform(sample)
        
        return sample


class CenterCrop(object):
    def __init__(self, output_size):
        self.output_size = output_size

    def __call__(self, sample):
        image, label = sample['image'], sample['label']

        # pad the sample if necessary
        if label.shape[0] <= self.output_size[0] or label.shape[1] <= self.output_size[1]:
            pw = max((self.output_size[0] - label.shape[0]) // 2 + 3, 0)
            ph = max((self.output_size[1] - label.shape[1]) // 2 + 3, 0)
            image = np.pad(image, [(pw, pw), (ph, ph)], mode='constant', constant_values=0)
            label = np.pad(label, [(pw, pw), (ph, ph)], mode='constant', constant_values=0)

        (w, h, d) = image.shape
        
        w1 = int(round((w - self.output_size[0]) / 2.))
        h1 = int(round((h - self.output_size[1]) / 2.))

        label = label[w1:w1 + self.output_size[0], h1:h1 + self.output_size[1]]
        image = image[w1:w1 + self.output_size[0], h1:h1 + self.output_size[1]]

        return {'image': image, 'label': label}


class RandomCrop(object):
    """
    Crop randomly the image in a sample
    Args:
    output_size (int): Desired output size
    """

    def __init__(self, output_size, with_sdf=False):
        self.output_size = output_size
        self.with_sdf = with_sdf

    def __call__(self, sample):
        image, label = sample['image'], sample['label']
        if self.with_sdf:
            sdf = sample['sdf']

        # pad the sample if necessary

        if label.shape[0] <= self.output_size[0] or label.shape[1] <= self.output_size[1] or label.shape[2] <= \
                self.output_size[2]:
            pd = max((self.output_size[0] - label.shape[0]) // 2 + 3, 0)
            pw = max((self.output_size[1] - label.shape[1]) // 2 + 3, 0)
            ph = max((self.output_size[2] - label.shape[2]) // 2 + 3, 0)

            image = np.pad(image, [(0, 0), (pw, pw), (ph, ph)], mode='constant', constant_values=0)
            label = np.pad(label, [(0, 0), (pw, pw), (ph, ph)], mode='constant', constant_values=0)
            

            if self.with_sdf:
                sdf = np.pad(sdf, [(0, 0), (pw, pw), (ph, ph)], mode='constant', constant_values=0)
        

        (d, w, h) = image.shape
        # if np.random.uniform() > 0.33:
        #     w1 = np.random.randint((w - self.output_size[0])//4, 3*(w - self.output_size[0])//4)
        #     h1 = np.random.randint((h - self.output_size[1])//4, 3*(h - self.output_size[1])//4)
        # else:
        w1 = np.random.randint(0, w - self.output_size[1])
        h1 = np.random.randint(0, h - self.output_size[2])
        label = label[:, w1:w1 + self.output_size[1], h1:h1 + self.output_size[2]]
        image = image[:, w1:w1 + self.output_size[1], h1:h1 + self.output_size[2]]
        if self.with_sdf:
            sdf = sdf[:,w1:w1 + self.output_size[1], h1:h1 + self.output_size[2]]
            return {'image': image, 'label': label, 'sdf': sdf}
        else:
            return {'image': image, 'label': label}


class RandomRotFlip(object):
    """
    Crop randomly flip the dataset in a sample
    Args:
    output_size (int): Desired output size
    """

    def __call__(self, sample):
        image, label = sample['image'], sample['label']
        k = np.random.randint(0, 4)
        for i in range(k):
            image = np.rot90(image, axes=(1, 2))
            label = np.rot90(label, axes=(1, 2))

        axis = np.random.randint(0, 2)
        image = np.flip(image, axis=axis).copy()
        label = np.flip(label, axis=axis).copy()

        return {'image': image, 'label': label}


class RandomNoise(object):
    def __init__(self, mu=0, sigma=0.1):
        self.mu = mu
        self.sigma = sigma

    def __call__(self, sample):
        image, label = sample['image'], sample['label']
        noise = np.clip(self.sigma * np.random.randn(image.shape[0], image.shape[1], image.shape[2]), -2*self.sigma, 2*self.sigma)
        noise = noise + self.mu
        image = image + noise
        return {'image': image, 'label': label}


class CreateOnehotLabel(object):
    def __init__(self, num_classes):
        self.num_classes = num_classes

    def __call__(self, sample):
        image, label = sample['image'], sample['label']
        onehot_label = np.zeros((self.num_classes, label.shape[0], label.shape[1], label.shape[2]), dtype=np.float32)
        for i in range(self.num_classes):
            onehot_label[i, :, :, :] = (label == i).astype(np.float32)
        return {'image': image, 'label': label,'onehot_label':onehot_label}


class ToTensor(object):
    """Convert ndarrays in sample to Tensors."""

    def __call__(self, sample):
        image = sample['image']
        # image = np.moveaxis(image, -1, 0).astype(np.float32)
        image = image.astype(np.float32)
        if 'onehot_label' in sample:
            a = {'image': torch.from_numpy(image), 'label': torch.from_numpy(sample['label']).long(),
                    'onehot_label': torch.from_numpy(sample['onehot_label']).long()}
            return a
        else:
            b = {'image': torch.from_numpy(image), 'label': torch.from_numpy(sample['label']).long()}

            return b


class TwoStreamBatchSampler(Sampler):
    """Iterate two sets of indices

    An 'epoch' is one iteration through the primary indices.
    During the epoch, the secondary indices are iterated through
    as many times as needed.
    """
    def __init__(self, primary_indices, secondary_indices, batch_size, secondary_batch_size):
        self.primary_indices = primary_indices
        self.secondary_indices = secondary_indices
        self.secondary_batch_size = secondary_batch_size
        self.primary_batch_size = batch_size - secondary_batch_size

        assert len(self.primary_indices) >= self.primary_batch_size > 0
        assert len(self.secondary_indices) >= self.secondary_batch_size > 0

    def __iter__(self):
        primary_iter = iterate_once(self.primary_indices)
        secondary_iter = iterate_eternally(self.secondary_indices)
        return (
            primary_batch + secondary_batch
            for (primary_batch, secondary_batch)
            in zip(grouper(primary_iter, self.primary_batch_size),
                    grouper(secondary_iter, self.secondary_batch_size))
        )

    def __len__(self):
        return len(self.primary_indices) // self.primary_batch_size

def iterate_once(iterable):
    return np.random.permutation(iterable)


def iterate_eternally(indices):
    def infinite_shuffles():
        while True:
            yield np.random.permutation(indices)
    return itertools.chain.from_iterable(infinite_shuffles())


def grouper(iterable, n):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3) --> ABC DEF"
    args = [iter(iterable)] * n
    return zip(*args)
from preprocess import preprocess
import gensim
import pandas as pd
import torch
import torch.utils.data as data

UNK_INDEX = 0

class Vocab:
    def __init__(self):
        # the minimum limit is 10000
        self.word2Vector = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin', binary=True, limit=10000)
        self.no_of_vocab = len(self.word2Vector.wv.vectors)
        self.embeddings_matrix = self.word2Vector.wv.vectors
        


def getVocab():
    vocab = Vocab()
    return vocab

class Dataset(data.Dataset):
    """Custom data.Dataset compatible with data.DataLoader."""

    def __init__(self, sent_in, sent_out, vocab):
        self.X = sent_in
        self.y = sent_out
        self.vocab = vocab
        self.num_total_seqs = len(self.X)
        # if (self.y is not None): self.y = torch.LongTensor(self.y)

    def __getitem__(self, index):
        """Returns one data pair (source and target)."""
        X = self.tokenize(self.X[index])
        if (self.y is not None):
            y = self.tokenize(self.y[index])
            return torch.LongTensor(X), torch.LongTensor(y)
        else:
            return torch.LongTensor(X)

    def __len__(self):
        return self.num_total_seqs

    def tokenize(self, sentence):
        #return [self.vocab.word2index[word] if word in self.vocab.word2index else UNK_INDEX for word in sentence]
        return [self.vocab.word2Vector.vocab.get(word).index if word in self.vocab.word2Vector.vocab else
                self.vocab.word2Vector.vocab.get("0").index for word in sentence]


def get_dataloaders(batch_size, max_len):
    vocab = getVocab()
    train_data_sent_in, train_data_sent_out = preprocess("dataset/micro/train.txt", windows=max_len)
    dev_data_sent_in, dev_data_sent_out = preprocess("dataset/micro/valid.txt", windows=max_len)
    test_data_sent_in, test_data_sent_out = preprocess("dataset/micro/test.txt", windows=max_len)
    train = Dataset(train_data_sent_in, train_data_sent_out, vocab)
    dev = Dataset(dev_data_sent_in, dev_data_sent_out, vocab)
    test = Dataset(test_data_sent_in, test_data_sent_out, vocab)
    data_loader_tr = torch.utils.data.DataLoader(dataset=train,
                                                 batch_size=batch_size,
                                                 shuffle=True)
    data_loader_dev = torch.utils.data.DataLoader(dataset=dev,
                                                  batch_size=batch_size,
                                                  shuffle=False)
    data_loader_test = torch.utils.data.DataLoader(dataset=test,
                                                   batch_size=batch_size,
                                                   shuffle=False)
    return data_loader_tr, data_loader_dev, data_loader_test, vocab.no_of_vocab, vocab.embeddings_matrix

    

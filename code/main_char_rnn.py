import numpy as np
import argparse
from tqdm import tqdm
import torch
import torch.nn as nn
from dataloader_char_rnn import get_dataloaders
from preprocess_char_rnn import clean_str
from RNN import RNNLM

use_gpu = torch.cuda.is_available()


def trainer(train_loader, dev_loader, model, optimizer, criterion, epoch=20, early_stop=5, scheduler=None):
    best_perp = 9999999
    for e in range(epoch):
        loss_log = []
        model.train()
        pbar = tqdm(enumerate(train_loader), total=len(train_loader))
        ######
        if use_gpu:
            model = model.cuda()
        #####
        for i, (seq_in, target) in pbar:
            # use gpu for training
            if use_gpu:
                seq_in = seq_in.cuda()
                target = target.cuda()
            optimizer.zero_grad()
            outputs, hidden = model(seq_in)
            loss = criterion(outputs, target.reshape(-1))
            loss.backward()
            optimizer.step()

            loss_log.append(loss.item())
            pbar.set_description("(Epoch {}) TRAIN LOSS:{:.4f}".format((e + 1), np.mean(loss_log)))

        model.eval()
        loss_log = []
        for seq_in, target in dev_loader:
            if use_gpu:
                seq_in = seq_in.cuda()
                target = target.cuda()
            outputs, hidden = model(seq_in)
            loss = criterion(outputs, target.reshape(-1))
            loss_log.append(loss.item())
        perp = np.exp(np.mean(loss_log))
        if perp < best_perp:
            best_perp = perp
        else:
            early_stop -= 1
        print("epcoh: {}, best perplexity:{} perplexity:{}".format(e + 1, best_perp, perp))
        if early_stop == 0:
            break
        if scheduler is not None:
            scheduler.step()
    return model, best_perp


def predict(model, vocab, start_vocab):
    model.eval()
    char_id = vocab.char2index[start_vocab]
    char = ""
    chars = []
    hidden = None
    while char != ">" and len(chars) < 100:
        input = torch.LongTensor([char_id]).reshape(1, 1)
        char = vocab.index2char[char_id]
        chars += [char]
        if use_gpu:
            input = input.cuda()
        output, hidden = model(input, hidden)
        char_id = torch.multinomial(torch.nn.Softmax(dim=0)(output), num_samples=1).item()
    print(''.join(chars))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--early_stop", type=int, default=10)
    parser.add_argument("--embed_dim", type=int, default=20)
    parser.add_argument("--dim_size", type=int, default=512)
    parser.add_argument("--num_layers", type=int, default=2)
    parser.add_argument("--window_size", type=int, default=25)
    parser.add_argument("--lr_decay", type=float, default=0.5)
    parser.add_argument("--amount_of_vocab", type=int, default=15000)
    args = parser.parse_args()

    # load data
    train_loader, dev_loader, test_loader, vocab_size, vocab = get_dataloaders(args.batch_size, args.window_size)
    # build model
    # try to use pretrained embedding here
    model = RNNLM(args, vocab_size, embedding_matrix=None)

    # loss function
    criterion = nn.CrossEntropyLoss()

    # choose optimizer
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr)

    # scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=args.lr_decay)
    model, best_perp = trainer(train_loader, dev_loader, model, optimizer, criterion, early_stop=args.early_stop)

    print('best_dev_perp:{}'.format(best_perp))
    predict(model, vocab, clean_str("T"))


if __name__ == "__main__":
    main()

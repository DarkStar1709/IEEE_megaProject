import json
import string
import numpy as np
from model import NeuralNet
from chatbot import tokenize, stem, bag_of_words
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
with open('mental_health_updated.json','r') as f:
    intents = json.load(f)
all_words = []
tags = []
xy = []
for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w,tag))
#print(tags)
ignore_words = string.punctuation
all_words= [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))
#print(tags)
X_train = []
y_train = []
for (pattern_sentence,tag)in xy:
    bag = bag_of_words(pattern_sentence,all_words)
    X_train.append(bag)

    label = tags.index(tag)
    y_train.append(label)
X_train = np.array(X_train)
y_train = np.array(y_train)

class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self,index):
        return self.x_data[index],self.y_data[index]
    def __len__(self):
        return  self.n_samples

batch_size = 8
hidden_size = 8
output_size = len(tags)
input_size = len(all_words)
learning_rate = 0.001
num_epochs = 1000



dataset = ChatDataset()
DataLoader: object
train_loader= DataLoader(dataset=dataset, batch_size= batch_size, shuffle=True)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size , hidden_size , output_size).to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)

# Learning rate scheduler
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5, factor=0.5)

# Training loop with validation
for epoch in range(num_epochs):
    model.train()
    for words, labels in train_loader:
        words, labels = words.to(device), labels.to(device)
        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # Validation step
    model.eval()
    with torch.no_grad():
        val_loss = 0
        for words, labels in train_loader:
            words, labels = words.to(device), labels.to(device)
            outputs = model(words)
            val_loss += criterion(outputs, labels).item()
        val_loss /= len(train_loader)

    # Learning rate adjustment
    scheduler.step(val_loss)

    if (epoch + 1) % 100 == 0:
        print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {loss.item():.4f}, Val Loss: {val_loss:.4f}')

print(f'final loss, loss={loss.item():.4f}')

data = {
    "model_state" : model.state_dict(),
    "input_size" : input_size,
    "output_size" : output_size,
    "hidden_size" : hidden_size,
    "all_words" : all_words,
    "tags" : tags
}
FILE = "datta.pth"
torch.save(data,FILE)

print(f'tarining complete. file saved to {FILE}')


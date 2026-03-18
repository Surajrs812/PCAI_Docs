import os
import time
import torch
import torchvision

from torchvision import transforms
from tqdm import tqdm

import torch.optim as optim
import torch.nn as nn

from torch.nn.parallel import DistributedDataParallel as DDP
import torch.distributed as dist
from torch.utils.data.distributed import DistributedSampler
from torch.utils.data import DataLoader, TensorDataset

dist.init_process_group("nccl")

local_rank = int(os.environ["LOCAL_RANK"])
global_rank = int(os.environ["RANK"])

BATCH_SIZE = 256 // int(os.environ["WORLD_SIZE"])
EPOCHS = 50
WORKERS = 24
IMG_DIMS = (64, 64)
CLASSES = 10


# Create Dummy Data to train the model on
X = torch.randn(10000, 10)  # 10000 samples, 10 features
y = torch.randn(10000, 1)   # 10000 labels

data = TensorDataset(X, y)

sampler = DistributedSampler(data)
data_loader = torch.utils.data.DataLoader(data,
                                          batch_size=BATCH_SIZE,
                                          shuffle=False,
                                          sampler=sampler,
                                          num_workers=WORKERS)

torch.cuda.set_device(local_rank)
torch.cuda.empty_cache()

# Simple network to train
class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(10, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

model = SimpleNN()

model = model.to('cuda:' + str(local_rank))

# Use the Distributed Data Parallel Wrapper
model = DDP(model, device_ids=[local_rank])

loss_fn = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# Train Loop
start = time.perf_counter()
for epoch in range(EPOCHS):
    epoch_start_time = time.perf_counter()

    model.train()
    for batch in tqdm(data_loader, total=len(data_loader)):
        features, labels = batch[0].to(local_rank), batch[1].to(local_rank)

        optimizer.zero_grad()

        preds = model(features)
        loss = loss_fn(preds, labels)

        loss.backward()
        optimizer.step()

    epoch_end_time = time.perf_counter()
    if global_rank == 0:
        print(f"Epoch {epoch+1} Time", epoch_end_time - epoch_start_time)
end = time.perf_counter()
if global_rank == 0:
    print("Training Took", end - start)


# torchrun --nnodes=x --nproc-per-node=y run_dist.py 
# Runs the script on x nodes with y GPUs per node
# Ex 2 nodes -> 2 machines with 8 process per node -> 8 GPUs per machine:
# 16 Total GPUs Used
import numpy as np
import torch
import matplotlib.pyplot as plt
from Hw3.Ex2.Utils import *
from Hw3.Ex2.model import *
import seaborn as sns
import torch.optim as optim
import pickle as pkl
import torchvision
from tqdm import tqdm
sns.set_style("darkgrid")


k = 0
beta = 0
batch_size = 128
n_epochs = 50
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = ConvVAE().to(device)
optimizer = optim.Adam(net.parameters(), lr=2e-4)
# scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3)
train_log = {}
val_log = {}
best_nll = np.inf
save_dir = './checkpoints/'


# Loading data
train_loader = torch.utils.data.DataLoader(SVHNDataset('train'), batch_size, shuffle=True)
val_loader = torch.utils.data.DataLoader(SVHNDataset('valid'), batch_size, shuffle=True)
test_loader = torch.utils.data.DataLoader(SVHNDataset('test'), batch_size, shuffle=True)


quick_plot = next(iter(train_loader))
img_grid = torchvision.utils.make_grid(quick_plot.cpu(), nrow=8).numpy()
plt.figure(figsize=(12, 12))
plt.imshow(np.transpose(img_grid, (1, 2, 0)))
plt.axis('off')
plt.savefig('./Hw3/Figures/SVHN_Figure.pdf')


# Training loop
for epoch in range(n_epochs):
    train_batch_loss = []
    for batch in tqdm(train_loader):
        net.train()
        batch = batch.to(device)
        loss, kl, nll = net.calc_loss(batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_log[k] = [loss.item(), kl.item(), nll.item()]
        train_batch_loss.append(loss.item())

        k += 1

    val_batch_loss = []
    for batch in tqdm(val_loader):
        with torch.no_grad():
            net.eval()
            loss, kl, nll = net.calc_loss(batch.to(device))
            val_log[k] = [loss.item(), kl.item(), nll.item()]
            val_batch_loss.append(loss.item())

    # scheduler.step(np.mean(val_batch_loss))
    if loss.item() < best_nll:
        best_nll = loss.item()
        save_checkpoint({'epoch': epoch, 'state_dict': net.state_dict()}, save_dir)

    print('[Epoch %d/%d][Step: %d] Train Loss: %s Test Loss: %s' \
          % (epoch + 1, n_epochs, k, np.mean(train_batch_loss), np.mean(val_batch_loss)))


# Plotting each minibatch step
x_val = list(val_log.keys())
values = np.array(list(val_log.values()))
loss_val, kl_val, recon_val = values[:, 0], values[:, 1], values[:, 2]

# Plot the loss graph
train_x_vals = np.arange(len(train_log))
values = np.array(list(train_log.values()))
loss_train, kl_train, recon_train = values[:, 0], values[:, 1], values[:, 2]

fig, ax = plt.subplots(1, 3, figsize=(10, 5))
ax[0].plot(train_x_vals, loss_train, label='Training ELBO')
ax[0].plot(x_val, loss_val, label='Validation ELBO')
ax[0].set_title('Training Curve')
ax[1].plot(train_x_vals, kl_train, label='Training KL')
ax[1].plot(x_val, kl_val, label='Validation KL')
ax[1].set_title('Kullback-Leibler Divergence Curve')
ax[2].plot(train_x_vals, recon_train, label='Training Reconstruction Error')
ax[2].plot(x_val, recon_val, label='Validation Reconstruction Error')
ax[2].set_title('Reconstruction Error Curve')
plt.legend(loc='best')

plt.xlabel('Num Steps')
plt.ylabel('NLL in bits per dim')
plt.savefig('./Hw3/Figures/Figure_8.pdf', bbox_inches='tight')
# plt.close()

# Load best and generate
load_checkpoint('./checkpoints/best.pth.tar', net)
quick_plot = next(iter(train_loader))[:100]
reconstructions_noise = net(quick_plot,noise=True)

fig, ax = plt.subplots(2, 1, figsize=(10, 5))
reconstructions_no_noise = net(quick_plot, noise=False)
img_grid = torchvision.utils.make_grid(reconstructions_no_noise.cpu().detach(), nrow=10).numpy()
ax[0].imshow(np.transpose(img_grid, (1, 2, 0)))
ax[0].axis('off')
ax[0].set_title('No decoder noise')

reconstructions = net(quick_plot)
img_grid = torchvision.utils.make_grid(reconstructions_noise.cpu().detach(), nrow=10).numpy()
ax[1].imshow(np.transpose(img_grid, (1, 2, 0)))
ax[1].axis('off')
ax[1].set_title('With decoder noise')
plt.savefig('./Hw3/Figures/Figure_9.pdf', bbox_inches='tight')



plt.figure(3)
X_sampled = net.sample(100)
img_grid = torchvision.utils.make_grid(X_sampled.cpu().detach(), nrow=10).numpy()
plt.figure(figsize=(12, 12))
plt.imshow(np.transpose(img_grid, (1, 2, 0)))
# plt.savefig('./Hw3/Figures/Figure_10.pdf', bbox_inches='tight')

load_checkpoint('./checkpoints/best.pth.tar', net)
fig, ax = plt.subplots(2, 1)
x = next(iter(test_loader))[:20]
interpolations, interpolations_mu = net.interpolations(x)

img_grid = torchvision.utils.make_grid(interpolations_mu.cpu().detach(), nrow=10).numpy()
ax[0].imshow(np.transpose(img_grid, (1, 2, 0)))
ax[0].set_title('No decoder noise')
ax[0].axis('off')

img_grid = torchvision.utils.make_grid(interpolations.cpu().detach(), nrow=10).numpy()
ax[1].imshow(np.transpose(img_grid, (1, 2, 0)))
ax[1].set_title('Decoder noise')
ax[1].axis('off')
fig.tight_layout()
plt.savefig('./Hw3/Figures/Figure_10.pdf', bbox_inches='tight')



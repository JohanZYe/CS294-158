import torch.optim as optim
import matplotlib.pyplot as plt
import seaborn as sns
from Hw2.Utils import *
from Hw2.model_complex import *

sns.set_style("darkgrid")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Data Loading
batch_size = 125
x, y = sample_data()
x_train = x[:int(len(x) * 0.8)]
train_loader = torch.utils.data.DataLoader(
    torch.from_numpy(x_train).float(), batch_size=batch_size, shuffle=True)
X_val = torch.from_numpy(x[int(len(x) * 0.8):]).float().to(device)

k = 0
net = RealNVP(8).to(device)
init_batch = torch.from_numpy(x_train).float().cuda()
net.initialize(init_batch)
# net = RealNVP(in_features=2, hidden_features=100, AC_layers=8).to(device)
optimizer = optim.Adam(net.parameters(), lr=1e-4)
n_epochs = 2
train_log = []
val_log = {}
best_nll = np.inf
save_dir = './checkpoints/'
prior = torch.distributions.MultivariateNormal(torch.zeros(2), torch.eye(2))


def calc_loss(log_determinant):
    """
    loss function for complex RealNVP
    :param log_determinant: Log_determinant from RealNVP
    :return: Rescaled log_determinant used for loss
    """
    loss = - log_determinant.mean() / (2 * np.log(2))
    return loss


# Training loop
for epoch in range(n_epochs):
    for batch in train_loader:
        batch = batch.to(device)
        z, log_determinant = net(batch)
        loss = calc_loss(log_determinant)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_log.append(loss.item())
        k += 1

    with torch.no_grad():
        z, log_determinant = net(X_val)
        loss = calc_loss(log_determinant)
        val_log[k] = loss.item()

    if loss.item() < best_nll:
        best_nll = loss.item()
        save_checkpoint({'epoch': epoch, 'state_dict': net.state_dict()}, save_dir)

    print('[Epoch %d/%d]\t[Step: %d]\tTrain Loss: %s\tTest Loss: %s' \
          % (epoch + 1, n_epochs, k, np.mean(train_log[-10:]), val_log[k]))

# Plotting each minibatch step
x_val = list(val_log.keys())
y_val = list(val_log.values())

# Plot the loss graph
train_x_vals = np.arange(len(train_log))
train_y_vals = train_log

fig, ax = plt.subplots(1, 3, figsize=(10, 5))
ax[0].plot(train_x_vals, train_y_vals, label='Training Error')
ax[0].plot(x_val, y_val, label='Validation Error')
ax[0].legend(loc='best')
ax[0].set_title('Training Curve')
ax[0].set_xlabel('Num Steps')
ax[0].set_ylabel('NLL in bits per dim')

# Latent visualization
load_checkpoint('./checkpoints/best.pth.tar', net)
with torch.no_grad():
    z, _ = net(torch.from_numpy(x).to(device).float())
z = z.cpu().detach().numpy()
ax[1].scatter(z[:, 0], z[:, 1], c=y)
ax[1].set_title("Latent space")

samples = torch.distributions.uniform.Uniform(-4,4).sample([5000, 2])
samples = samples.to(device).float()
for i in reversed(range(len(net.layers))):
    samples = net.layers[i](samples, forward=False)
samples = samples.detach().cpu()
ax[2].scatter(samples[:, 0], samples[:, 1], s=9)


# Load best and generate + visualize latent space
# axis = np.linspace(-4, 4, 100)
# samples = np.array(np.meshgrid(axis, axis)).T.reshape([-1, 2])
# samples = torch.from_numpy(samples).to(device).float()  # GPU, tensor Conversion stuff
# with torch.no_grad():
#     z, jacobian = net(samples)
#
# pdf = torch.exp(jacobian).cpu().numpy().reshape(100, 100)
# ax[2].imshow(np.rot90(pdf, 1))
# ax[2].set_xticks([])
# ax[2].set_yticks([])
# ax[2].set_title("Best distribution on validation set")
# plt.savefig('./Hw2/Figures/Figure_6.pdf', bbox_inches='tight')


import numpy as np
import torch
import matplotlib.pyplot as plt
from Hw3.Ex1.Utils import *
from Hw3.Ex1.model import *
import seaborn as sns
import torch.optim as optim

sns.set_style("darkgrid")

ds1 = False
ds2 = True
k = 0
beta = 0
batch_size = 125
n_epochs = 10
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = VariationalAutoEncoder(vector=True).to(device)
optimizer = optim.Adam(net.parameters(), lr=2e-4)
train_log = {}
val_log = {}
best_nll = np.inf
save_dir = './checkpoints/'

fig, ax = plt.subplots(1, 2)
# Data set 1
x1 = sample_data_1()
ax[0].scatter(x1[:, 0], x1[:, 1])
ax[0].set_title('Data set 1')

# Data set 2
x2 = sample_data_2()
ax[1].scatter(x2[:, 0], x2[:, 1])
ax[1].set_title('Data set 2')
plt.savefig('./Hw3/Figures/Figure_1.pdf', bbox_inches='tight')

if ds1:
    train_loader = torch.utils.data.DataLoader(torch.from_numpy(x1[:int(len(x1) * 0.8)]).float(), batch_size=batch_size,
                                               shuffle=True)
    X_val = torch.from_numpy(x1[int(len(x1) * 0.8):]).to(device).float()
else:
    train_loader = torch.utils.data.DataLoader(torch.from_numpy(x2[:int(len(x2) * 0.8)]).float(), batch_size=batch_size,
                                               shuffle=True)
    X_val = torch.from_numpy(x2[int(len(x2) * 0.8):]).to(device).float()

# Training loop
for epoch in range(n_epochs):
    batch_loss = []
    for batch in train_loader:
        net.train()
        batch = batch.to(device)
        loss, kl, nll = net.calc_loss(batch, beta)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_log[k] = [loss.item(), nll.item(), kl.item()]
        batch_loss.append(loss.item())

        k += 1
        if 1 > beta:
            beta += 0.001

    with torch.no_grad():
        net.eval()
        loss, kl, nll = net.calc_loss(X_val, beta)
        val_log[k] = [loss.item(), nll.item(), kl.item()]

    if loss.item() < best_nll:
        best_nll = loss.item()
        save_checkpoint({'epoch': epoch, 'state_dict': net.state_dict()}, save_dir)

    print('[Epoch %d/%d][Step: %d] Train Loss: %s Test Loss: %s' \
          % (epoch + 1, n_epochs, k, np.mean(batch_loss), val_log[k][0]))

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
ax[0].legend(loc='best')
ax[0].set_title('Training Curve')
ax[0].set_xlabel('Num Steps')
ax[0].set_ylabel('NLL in bits per dim')

ax[1].plot(train_x_vals, kl_train, label='Training KL')
ax[1].plot(x_val, kl_val, label='Validation KL')
ax[1].legend(loc='best')
ax[1].set_title('Kullback-Leibler Curve')
ax[1].set_xlabel('Num Steps')
ax[1].set_ylabel('KL-Divergence')

ax[2].plot(train_x_vals, recon_train, label='Training Reconstruction Error')
ax[2].plot(x_val, loss_val, label='Validation Reconstruction Error')
ax[2].legend(loc='best')
ax[2].set_title('Reconstruction Error curve')
ax[2].set_xlabel('Num Steps')
ax[2].set_ylabel('Reconstruction Error')
plt.savefig('Figure_1.pdf', bbox_inches='tight')


# Load best and generate
load_checkpoint('./checkpoints/best.pth.tar', net)
samples = net.sample(1000, decoder_noise=False).detach().cpu().numpy()
fig, ax = plt.subplots(1, 2, figsize=(10, 5))
ax[0].scatter(samples[:, 0], samples[:, 1])
ax[0].set_title("No decoder noise")
plt.savefig('./Hw2/Figures/Figure_2.pdf', bbox_inches='tight')

samples = net.sample(1000, decoder_noise=True).detach().cpu().numpy()
ax[1].scatter(samples[:, 0], samples[:, 1])
ax[1].set_title("Decoder noise")
plt.savefig('./Hw2/Figures/Figure_2.pdf', bbox_inches='tight')

#
# # Latent visualization
# x, y = sample_data()
# x = torch.from_numpy(x).float().to(device)
# pi, mu, var = net(x)
# z = net.Latent(x, pi, mu, var).cpu().detach().numpy()
#
# plt.figure(3)
# plt.scatter(z[:, 0], z[:, 1], c=y)
# plt.savefig('./Hw2/Figures/Figure_3.pdf', bbox_inches='tight')
#

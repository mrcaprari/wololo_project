# Prendere output da grafo trasformato

# Calcolare loss in parallelo

# Calcolare media loss

# Calcolare KL divergence

# Sommare

# Ottimizzare


# Test
import torch
from torch import nn
from converter_project.transformations import GaussianTransformation
from converter_project.converters import ModuleConverter
from tqdm import tqdm


def BBVI(
        starting_model, 
        n_samples, 
        epochs, 
        dataloader, 
        loss_fn, 
        optimizer_fn, 
        learning_rate, 
        kl_weight,
        transform_list = []
        ):
    model = ModuleConverter(GaussianTransformation()).convert(starting_model, transform_list)
    optimizer = optimizer_fn(model.parameters(), lr=learning_rate)

    pred_history = []
    kl_history = []
    total_history = []

    for epoch in range(epochs):
        with tqdm(total=len(dataloader), desc=f"Epoch {epoch + 1}/{epochs}") as pbar:
            for x_batch, y_batch in dataloader:
                pred_loss, kl_loss, total_loss = BBVI_step(model, n_samples, x_batch, y_batch, loss_fn, optimizer, kl_weight)

                pred_history.append(pred_loss.detach().cpu().numpy())
                kl_history.append(kl_loss.detach().cpu().numpy())
                total_history.append(total_loss.detach().cpu().numpy())
                
                pbar.set_postfix(tot_loss=total_loss.item(),
                                 pred = pred_loss.item(),
                                 kernel = kl_loss.item())
                pbar.update(1)
        
    return model, pred_history, kl_history, total_history

def BBVI_step(
        model, 
        n_samples, 
        x, 
        y, 
        loss_fn, 
        optimizer,
        kl_weight
        ):
    
    optimizer.zero_grad()    
    output = model(x, n_samples)
    pred_loss = torch.vmap(loss_fn, in_dims=(0, None))(output, y).mean()
    kl_loss = model.kl_divergence() * kl_weight
    total_loss = pred_loss + kl_loss 
    total_loss.backward()
    optimizer.step()
    return pred_loss, kl_loss, total_loss

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import Optimizer
import numpy as np
from torch.utils.data.dataset import random_split
from model.loss import YoloV3Loss
from utils import scale_anchors

class Model:
    def __init__(
        self, 
        model: nn.Module, 
        loss_fn: YoloV3Loss, 
        optimizer: Optimizer, 
        dataset: Dataset,
        train_val_split: tuple,
        batch_size: int,
        device: str,
        scales: torch.Tensor,
        anchors: torch.Tensor,
        ):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.t_dataset, self.v_dataset = random_split(dataset, train_val_split)
        self.t_dataloader = DataLoader(self.t_dataset, batch_size, shuffle=True)
        self.v_dataloader = DataLoader(self.v_dataset, batch_size, shuffle=False)
        self.device = device
        self.history = {
            "box_loss": [],
            "object_loss": [],
            "no_object_loss": [],
            "class_loss": [],
            "total_loss": [],
        }
        self.val_history = {
            "box_loss": [],
            "object_loss": [],
            "no_object_loss": [],
            "class_loss": [],
            "total_loss": [],
        }
        self.scales = scales.to(device)
        self.anchors = anchors.to(device)
        _, self.img_height, self.img_width = dataset.__getitem__(1)[0].shape

    def train_one_epoch(self, epoch):
        epoch_history = {
            "box_loss": 0.,
            "object_loss": 0.,
            "no_object_loss": 0.,
            "class_loss": 0.,
            "total_loss": 0.
        }

        for batch_num, (images, targets) in enumerate(self.t_dataloader):

            images = images.to(self.device)
            targets = [target.to(self.device) for target in targets]

            if batch_num + 1 % 5 == 0:
                batch_loss = np.round(epoch_history['total_loss'], 3)
                batch_loss = batch_loss // (batch_num + 1)
                print(f"BATCH {batch_num} LOSS {batch_loss}")

            self.optimizer.zero_grad()

            predicitons = self.model(images)
            
            batch_loss = torch.zeros(1).to(self.device)
            for scale_id, (preds, targs) in enumerate(zip(predicitons, targets)):
                
                scaled_anchors = scale_anchors(
                    self.anchors[scale_id: scale_id + 3], 
                    self.scales[scale_id],
                    self.img_width, self.img_height,
                    device=self.device
                )

                _batch_loss, batch_history = self.loss_fn(
                    preds, 
                    targs,
                    scaled_anchors
                )
                batch_loss += _batch_loss

                for key in epoch_history.keys():
                    epoch_history[key] += batch_history[key]

            batch_loss.backward()

            self.optimizer.step()

        for key in self.history.keys():
            self.history[key].append(epoch_history[key] / len(self.t_dataset))

        print(f"EPOCH {epoch} AVG LOSS {np.round(epoch_history['total_loss'], 3)}")

        return None

    def validate_one_epoch(self, epoch):
        val_epoch_history = {
            "box_loss": 0.,
            "object_loss": 0.,
            "no_object_loss": 0.,
            "class_loss": 0.,
            "total_loss": 0.
        }
        for images, targets in self.v_dataloader:

            images = images.to(self.device)
            targets = [target.to(self.device) for target in targets]

            with torch.no_grad():
                predicitons = self.model(images)
                for scale_id, (preds, targs) in enumerate(zip(predicitons, targets)):

                    scaled_anchors = scale_anchors(
                        self.anchors[scale_id: scale_id + 3], 
                        self.scales[scale_id],
                        self.img_width, self.img_height,
                        device=self.device
                    )

                    _, val_history = self.loss_fn(
                        preds, 
                        targs, 
                        scaled_anchors
                    )

                    for key in val_epoch_history.keys():
                        val_epoch_history[key] += val_history[key]

        for key in val_epoch_history.keys():
            self.val_history[key].append(val_epoch_history[key] / len(self.v_dataset))

        print(f"EPOCH {epoch} AVG VAL LOSS {np.round(val_epoch_history['total_loss'], 3)}")

        return None

    def fit(self, num_epochs):
        for i in range(1, num_epochs + 1):

            self.model.train()
            self.train_one_epoch(epoch=i)

            self.model.eval()
            self.validate_one_epoch(epoch=i)

        return None
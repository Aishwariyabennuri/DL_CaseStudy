import torch
import torch.nn as nn
import torch.nn.functional as functional

ACT_RELU = "relu"
ACT_LEAKY_RELU = "leaky_relu"
ACT_ELU = "elu"
ACT_NONE = "none"


class ABN(nn.Module):
    """Activated Batch Normalization in pure PyTorch (no C++ extensions needed)"""

    def __init__(self, num_features, eps=1e-5, momentum=0.1, affine=True, activation="leaky_relu", slope=0.01):
        super(ABN, self).__init__()
        self.num_features = num_features
        self.affine = affine
        self.eps = eps
        self.momentum = momentum
        self.activation = activation
        self.slope = slope
        if self.affine:
            self.weight = nn.Parameter(torch.ones(num_features))
            self.bias = nn.Parameter(torch.zeros(num_features))
        else:
            self.register_parameter('weight', None)
            self.register_parameter('bias', None)
        self.register_buffer('running_mean', torch.zeros(num_features))
        self.register_buffer('running_var', torch.ones(num_features))
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.constant_(self.running_mean, 0)
        nn.init.constant_(self.running_var, 1)
        if self.affine:
            nn.init.constant_(self.weight, 1)
            nn.init.constant_(self.bias, 0)

    def forward(self, x):
        x = functional.batch_norm(x, self.running_mean, self.running_var, self.weight, self.bias,
                                  self.training, self.momentum, self.eps)

        if self.activation in [ACT_RELU, "relu"]:
            return functional.relu(x, inplace=True)
        elif self.activation in [ACT_LEAKY_RELU, "leaky_relu"]:
            return functional.leaky_relu(x, negative_slope=self.slope, inplace=True)
        elif self.activation in [ACT_ELU, "elu"]:
            return functional.elu(x, inplace=True)
        else:
            return x

    def __repr__(self):
        rep = '{name}({num_features}, eps={eps}, momentum={momentum},' \
              ' affine={affine}, activation={activation}'
        if self.activation in ["leaky_relu", ACT_LEAKY_RELU]:
            rep += ', slope={slope})'
        else:
            rep += ')'
        return rep.format(name=self.__class__.__name__, **self.__dict__)


class InPlaceABN(ABN):
    def forward(self, x):
        return super(InPlaceABN, self).forward(x)


class InPlaceABNSync(ABN):
    def forward(self, x):
        return super(InPlaceABNSync, self).forward(x)

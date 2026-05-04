import random
import math

class MLP:
    def __init__(self):
        self.W1 = [[random.gauss(0, 0.1) for i in range(32)] for j in range(16)]
        self.b1 = [0 for i in range(32)]
        self.W2 = [[random.gauss(0, 0.1) for i in range(16)] for j in range(32)]
        self.b2 = [0 for i in range(16)]
        self.W3 = [[random.gauss(0, 0.1) for i in range(4)] for j in range(16)]
        self.b3 = [0 for i in range(4)]

    def relu(self, x):
        y = [max(0, i) for i in x]
        return y
    
    def softmax(self, x):
        exp_x = [math.exp(i) for i in x]
        sum_exp_x = sum(exp_x)
        return [i / sum_exp_x for i in exp_x]
    
    def matmul(self, x, W):
        output = []
        for j in range(len(W[0])):
            sum = 0
            for i in range(len(x)):
                sum += x[i] * W[i][j]
            output.append(sum)
        return output
    
    def forward(self, x):
        y = []
        for batch in x:
            z1 = self.matmul(batch, self.W1)
            z1 = [z1[i] + self.b1[i] for i in range(len(z1))]
            a1 = self.relu(z1)

            z2 = self.matmul(a1, self.W2)
            z2 = [z2[i] + self.b2[i] for i in range(len(z2))]
            a2 = self.relu(z2)

            z3 = self.matmul(a2, self.W3)
            z3 = [z3[i] + self.b3[i] for i in range(len(z3))]
            a3 = self.softmax(z3)
            y.append(a3)

        return y

if __name__ == "__main__":
    m = MLP()

    batch = [
        [random.random() for _ in range(16)]
        for _ in range(5)
    ]

    out = m.forward(batch)

    print("Batch size:", len(batch))
    print("Output size:", len(out))
    print("Each output length:", len(out[0]))

    for i, o in enumerate(out):
        print(f"Sample {i} sum:", sum(o))
        print(f"Sample {i} output:", o)
        print("---")
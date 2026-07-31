# NEGATIVE CONTROL: code with no absence-dressing at all. Detector must stay quiet.
def classify(x):
    if x is None:
        raise ValueError("no measurement")
    return "green" if x < 1.0 else "gray"
def add(a, b):
    total = a + b
    return total

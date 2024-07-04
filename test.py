from data import generate_R, generate_G, generate_Vkt
from model import optimize_model

def main():
    N = [i for i in range(1, 15)]
    C1, C2, C3 = 100, 50, 100
    fc = lambda c: 200 + 50 * c
    gc = lambda c: 300 + 300 * c
    hc = lambda c: 200 + 30 * c
    theta = 10
    r = 30
    TC = 2
    TB = 1/6
    Ttol = 1/2
    epsilon = 0.8
    w = 0.0365
    OB, OE = 6, 23
    observed_days = 30

    edges = [
        (1, 2, 1),
        (2, 3, 3.5),
        (3, 4, 14),
        (4, 5, 3.8),
        (5, 6, 17.5),
        (6, 7, 14.5),
        (7, 8, 4.1),
        (8, 9, 6.9),
        (9, 10, 15.5),
        (10, 11, 3.3),
        (11, 12, 10.7),
        (12, 13, 13),
        (13, 14, 2.7),
        (14, 1, 7.9)
    ]

    R = generate_R()
    d, a, Tij = generate_G(edges)
    V_kt = generate_Vkt(observed_days, epsilon, R)
    optimize_model(N, C1, C2, C3, fc, gc, hc, theta, r, TC, TB, Ttol, epsilon, w, OB, OE, observed_days, d, a, Tij, V_kt)

if __name__ == "__main__":
    main()
import clifford
from clifford.g3c import *
import numpy as np
from pyganja import *


def init_base_matrix():
    base_matrix = np.zeros([8, 8])
    for i in range(0, 8):
        base_matrix[i, 7 - i] = -1
    base_matrix[3, 3] = 1
    base_matrix[4, 4] = 1
    base_matrix[3, 4] = 0
    base_matrix[4, 3] = 0
    return base_matrix


def points_close_to_horizontal_ellipse(a, b, u, v):
    points = []
    x = u - a + 1e-4
    d = 2 * a / 15
    while x < u + a - 1e-4:
        y = np.sqrt(1 - (x - u) ** 2 / a ** 2) * b + v
        # points.append(p_vector(x + 0.01 * np.random.random(), y + 0.01 * np.random.random()))
        points.append(p_vector(x, y))
        x += d
    return np.array(points)


def init_p_matrix(points_natrix):
    p_matrix = np.zeros([8, 8])
    l = len(points_natrix[0])
    for i in range(0, len(points_natrix)):
        p_matrix += np.matmul(points_natrix[i].reshape(l, 1), points_natrix[i].reshape(1, l))
    b_matrix = init_base_matrix()
    p_matrix = np.matmul(b_matrix, np.matmul(p_matrix, b_matrix))
    return p_matrix


def p_vector(x, y):
    return np.array([0, 0, 1, x, y, 0.5 * (x ** 2 + y ** 2), 0.5 * (x ** 2 - y ** 2), x * y])


def conic_of_matrix_p(p_matrix):
    p_0_inv = np.linalg.inv(p_matrix[:2, :2])
    p_1 = p_matrix[:2, 2:6]
    p_c = p_matrix[2:6, 2:6]
    b_c = init_base_matrix()[2:6, 2:6]
    p_con = np.matmul(b_c, p_c - np.matmul(p_1.transpose(), np.matmul(p_0_inv, p_1)))
    eig_vals_and_vecs = np.linalg.eig(p_con)
    vals = eig_vals_and_vecs[0]
    index_of_eig_value = np.where(vals == vals[np.where(vals >= 0)[0]].min())[0][0]
    eig_vec = eig_vals_and_vecs[1][:, index_of_eig_value]
    w_vec = -np.matmul(p_0_inv, np.matmul(p_1, eig_vec))
    return eig_vec, w_vec


def from_pm_to_inf0(p: float, m: float) -> tuple:
    return 0.5 * (p + m), m - p


def rotor_cra(theta):
    return np.cos(theta / 2) - e12 * np.sin(theta / 2)


def translator_cra(t):
    return 1 - 0.5 * t * einf


def rotor_and_rotor_inv_gac(psi):
    rp = np.cos(psi / 2) * N + np.sin(psi / 2) * w1x1(E1, E2)
    rp_ = np.cos(psi / 2) * N - np.sin(psi / 2) * w1x1(E1, E2)
    r1wr2 = np.cos(psi) ** 2 * N - np.sin(psi) * np.cos(psi) * w1x1(F0, Ginf) + np.sin(psi) * np.cos(psi) * w1x1(G0, Finf) - np.sin(psi) ** 2 * w1x1(G0, w1x2(Finf, w1x1(F0, Ginf)))
    r1wr2_ = np.cos(psi) ** 2 * N - np.sin(psi) * np.cos(psi) * w1x1(G0, Finf) + np.sin(psi) * np.cos(psi) * w1x1(F0, Ginf) - np.sin(psi) ** 2 * w1x1(F0, w1x2(Ginf, w1x1(G0, Finf)))
    return np.matmul(rp, r1wr2), np.matmul(r1wr2_, rp_)


def translator_and_translator_inv_gac(u, v):
    t_u = np.matmul(N - 0.5 * u * w1x1(E1, Einf),
                    np.matmul(N - 0.5 * u * w1x1(E1, Finf) + 0.25 * u ** 2 * w1x1(Einf, Finf),
                              N - 0.5 * u * w1x1(E2, Ginf)))

    t_u_inv = np.matmul(N + 0.5 * u * w1x1(E2, Ginf),
                        np.matmul(N + 0.5 * u * w1x1(E1, Finf) - 0.25 * u ** 2 * w1x1(Einf, Finf),
                                  N + 0.5 * u * w1x1(E1, Einf)))

    t_v = np.matmul(N - 0.5 * v * w1x1(E2, Einf),
                    np.matmul(N + 0.5 * v * w1x1(E2, Finf) - 0.25 * v ** 2 * w1x1(Einf, Finf),
                              N - 0.5 * v * w1x1(E1, Ginf)))

    t_v_inv = np.matmul(N + 0.5 * v * w1x1(E1, Ginf),
                        np.matmul(N - 0.5 * v * w1x1(E2, Finf) + 0.25 * v ** 2 * w1x1(Einf, Finf),
                                  N + 0.5 * v * w1x1(E2, Einf)))

    return np.matmul(t_u, t_v), np.matmul(t_v_inv, t_u_inv)


def w1x1(v1, v2):
    return 0.5 * (np.matmul(v1, v2) - np.matmul(v2, v1))


def w1x2(v1, v2):
    return 0.5 * (np.matmul(v1, v2) + np.matmul(v2, v1))


def w1xn(v1, v2, n):
    return 0.5 * (np.matmul(v1, v2) + (- 1) ** n * np.matmul(v2, v1))


def wnx1(v1, v2, n):
    return (-1) ** n * w1xn(v2, v1, n)


def s1x1(v1, v2):
    return 0.5 * (np.matmul(v1, v2) + np.matmul(v2, v1))


def wedge_of_n_vectors(vectors):
    vector = vectors[-1]
    n = len(vectors)
    for i in range(1, n):
        vector = w1xn(vectors[-1-i], vector, i)
    return vector


def multiplication_of_n_vectors(vectors):
    vector = vectors[0]
    for i in range(1, len(vectors)):
        vector = np.matmul(vector, vectors[i])
    return vector


def coefficients_of_object_in_matrix(matrix: clifford._mvarray.MVArray) -> np.ndarray:
    coeffs = np.zeros(8)
    cra_object_values = matrix[0, 0].value
    coeffs[0:2] = cra_object_values[1:3]
    coeffs[2], coeffs[3] = from_pm_to_inf0(cra_object_values[4], cra_object_values[5])
    coeffs[4] = 0.5 * matrix[0, 1].value[0]
    coeffs[5] = - matrix[1, 0].value[0]
    coeffs[6] = 0.5 * matrix[0, 2].value[0]
    coeffs[7] = - matrix[2, 0].value[0]
    return coeffs


def init_cra_vector_as_matrix(cra_vector: clifford._multivector.MultiVector) -> clifford._mvarray.MVArray:
    matrix_object = np.eye(4)
    matrix_object[1, 1] = -1
    matrix_object[2, 2] = -1
    return cra_vector * matrix_object


def init_point_gac(x, y):
    return E0 + x * E1 + y * E2 + 0.5 * (x ** 2 + y ** 2) * Einf + 0.5 * (x ** 2 - y ** 2) * Finf + x * y * Ginf


def init_conic(center_x: float, center_y: float, axis_a: float, axis_b: float, theta: float) -> clifford._mvarray.MVArray:
    if axis_b > 0:
        return init_ellipse(center_x, center_y, axis_a, axis_b, theta)
    elif axis_b < 0:
        return init_hyperbola(center_x, center_y, axis_a, -axis_b, theta)
    else:
        return init_parabola(center_x, center_y, axis_a, theta)


def init_ellipse(center_x: float, center_y: float, axis_a: float, axis_b: float, theta: float) -> clifford._mvarray.MVArray:
    alpha = (axis_a ** 2 - axis_b ** 2) / (axis_a ** 2 + axis_b ** 2)
    beta = 2 * axis_a ** 2 * axis_b ** 2 / (axis_a ** 2 + axis_b ** 2)
    return init_conic_special(center_x, center_y, alpha, beta, theta)


def init_hyperbola(center_x: float, center_y: float, axis_a: float, axis_b: float, theta: float) -> clifford._mvarray.MVArray:
    alpha = (axis_a ** 2 + axis_b ** 2) / (axis_a ** 2 - axis_b ** 2)
    beta = -2 * axis_a ** 2 * axis_b ** 2 / (axis_a ** 2 - axis_b ** 2)
    return init_conic_special(center_x, center_y, alpha, beta, theta)


def init_conic_special(u: float, v: float, alpha: float, beta: float, theta: float) -> clifford._mvarray.MVArray:
    k_1 = u - u * alpha * np.cos(2 * theta)\
          - v * alpha * np.sin(2 * theta)
    k_2 = v + v * alpha * np.cos(2 * theta)\
          - u * alpha * np.sin(2 * theta)
    k_3 = 0.5 * (u ** 2 + v ** 2 - beta
                 - (u ** 2 - v ** 2) * alpha * np.cos(2 * theta)
                 - 2 * u * v * alpha * np.sin(2 * theta))
    k_4 = 1
    k_6 = - alpha * np.cos(2 * theta)
    k_8 = - alpha * np.sin(2 * theta)
    return k_1 * E1 + k_2 * E2 + k_3 * Einf + k_4 * E0\
           + k_6 * F0 + k_8 * G0


def init_parabola(u, v, p, theta):
    k_1 = u + u * np.cos(2 * theta) + v * np.sin(2 * theta)\
            - 2 * p * np.sin(theta)
    k_2 = v - v * np.cos(2 * theta) + u * np.sin(2 * theta)\
            + 2 * p * np.cos(theta)
    k_3 = 0.5 * (u ** 2 + v ** 2
                 + (u ** 2 - v ** 2) * np.cos(2 * theta)
                 + 2 * u * v * np.sin(2 * theta)
                 - 4 * p * u * np.sin(theta)
                 + 4 * p * v * np.cos(theta))
    k_4 = 1
    k_6 = np.cos(2 * theta)
    k_8 = np.sin(2 * theta)
    return k_1 * E1 + k_2 * E2 + k_3 * Einf + k_4 * E0\
           + k_6 * F0 + k_8 * G0


def parameters_of_conic(conic):
    identification = identify_conic(conic)
    params = {}
    if identification == "hyperbola":
        params = parameters_of_hyperbola(conic)
    elif identification == "parabola":
        params = parameters_of_parabola(conic)
    elif identification == "ellipse":
        params = parameters_of_ellipse(conic)
    params["conic"] = identification
    return params

def identify_conic(conic):
    k = coefficients_of_object_in_matrix(norm_conic(conic))
    alpha = np.sqrt(k[5] ** 2 + k[7] ** 2)
    eps = 1e-6
    if alpha > 1 + eps:
        return "hyperbola"
    elif np.abs(alpha - 1) < eps:
        return "parabola"
    elif alpha > 0:
        return "ellipse"
    else:
        return "singular_situation"


def parameters_of_parabola(parabola):
    k = coefficients_of_object_in_matrix(norm_conic(parabola))
    theta = 0.5 * compute_angle(k[5], k[7])
    rot, rot_inv = rotor_and_rotor_inv_gac(theta - np.pi / 2)
    parab_rot = np.matmul(rot, np.matmul(norm_conic(parabola), rot_inv))
    k_rot = coefficients_of_object_in_matrix(norm_conic(parab_rot))
    sign = 1
    if k_rot[0] > 0:
        sign = -1
    p = np.abs(0.5 * k_rot[0])
    v_rot = 0.5 * k_rot[1]
    u_rot = (2 * k_rot[2] - 0.5 * k_rot[1] ** 2) / (-4 * p * sign)
    apex = rotor_cra(theta - np.pi / 2) * (u_rot * e1 + v_rot * e2) * rotor_cra(-theta + np.pi / 2)
    if sign == -1:
        theta = theta + (-sign_of_theta(theta)) * np.pi

    return {"u": apex.value[1], "v": apex.value[2], "p": p, "theta": theta}


def norm_conic(conic: clifford._mvarray.MVArray) -> clifford._mvarray.MVArray:
    return conic / from_pm_to_inf0(conic[0, 0].value[4], conic[0, 0].value[5])[1]


def parameters_of_ellipse(ellipse: clifford._mvarray.MVArray) -> dict:
    param_con = parameters_of_conic_special(ellipse)
    a = np.sqrt(param_con["beta"] / (1 - param_con["alpha"]))
    b = np.sqrt(param_con["beta"] / (1 + param_con["alpha"]))
    return {"center_x": param_con["u"], "center_y": param_con["v"], "axis_a": a, "axis_b": b, "theta": param_con["theta"]}


def parameters_of_hyperbola(hyperbola: clifford._mvarray.MVArray) -> dict:
    param_con = parameters_of_conic_special(hyperbola)
    if param_con["beta"] > 0:
        param_con["alpha"] *= -1
        param_con["theta"] = param_con["theta"] + (-sign_of_theta(param_con["theta"])) * np.pi / 2
    a = np.sqrt(param_con["beta"] / (1 - param_con["alpha"]))
    b = np.sqrt(-param_con["beta"] / (1 + param_con["alpha"]))
    return {"center_x": param_con["u"], "center_y": param_con["v"], "axis_a": a, "axis_b": b, "theta": param_con["theta"]}


def sign_of_theta(theta):
    sign = np.sign(theta)
    if sign == 0:
        return 1
    else:
        return sign


def parameters_of_conic_special(conic: clifford._mvarray.MVArray) -> dict:
    k = coefficients_of_object_in_matrix(norm_conic(conic))
    alpha = np.sqrt(k[5] ** 2 + k[7] ** 2)
    theta = 0.5 * compute_angle(- k[5] / alpha, -k[7] / alpha)
    c1 = 1 - alpha * np.cos(2 * theta)
    c2 = -alpha * np.sin(2 * theta)
    c3 = 1 + alpha * np.cos(2 * theta)
    x = np.matmul(np.linalg.inv(np.array([[c1, c2], [c2, c3]])), np.array([k[0], k[1]]))
    u, v = x[0], x[1]
    beta = u ** 2 + v ** 2 - (u ** 2 - v ** 2) * alpha * np.cos(2 * theta) - 2 * u * v * alpha * np.sin(2 * theta) - 2 * k[2]
    return {"u": u, "v": v, "alpha": alpha, "beta": beta, "theta": theta}


def compute_angle(cos_angle: float, sin_angle: float) -> float:
    angle = np.arccos(cos_angle)
    if np.sign(np.arcsin(sin_angle)) >= 0:
        return angle
    else:
        return -angle


def points_of_ipns_cra_point_pair(point_pair):
    line = Icra * ((Icra * point_pair) ^ einf)
    radius = np.sqrt((-point_pair * point_pair / ((point_pair ^ einf) ** 2).value[0]).value[0])
    t = radius * (line.value[2] * e1 - line.value[1] * e2) / np.sqrt(line.value[2] ** 2 + line.value[1] ** 2)
    center = point_pair * einf * point_pair
    tr = translator_cra(t)
    point1 = corrected_point(tr * center * ~tr)
    point2 = corrected_point(~tr * center * tr)
    return point1, point2


def norm_point(point):
    return point / from_pm_to_inf0(point.value[4], point.value[5])[1]


def corrected_point(point):
    p = norm_point(point)
    return up(p.value[1] * e1 + p.value[2] * e2)


def elements_of_conic(conic):
    identification = identify_conic(conic)
    if identification == "hyperbola":
        return elements_of_hyperbola(conic, 300, 50)
    elif identification == "parabola":
        return elements_of_parabola(conic, 50, 10)
    elif identification == "ellipse":
        return elements_of_ellipse(conic, 100)
    else:
        return identification


def elements_of_ellipse(ellipse, pieces):
    params = parameters_of_ellipse(ellipse)
    t = params["center_x"] * e1 + params["center_y"] * e2
    center = up(t)
    motor = translator_cra(t) * rotor_cra(params["theta"])
    excentricity = np.sqrt(params["axis_a"] ** 2 - params["axis_b"] ** 2)

    focus1 = corrected_point(motor * up(excentricity * e1) * ~motor)
    focus2 = corrected_point(motor * up(-excentricity * e1) * ~motor)
    points_of_ellipse = [corrected_point(motor * up(-params["axis_a"] * e1) * ~motor),
                         corrected_point(motor * up(params["axis_a"] * e1) * ~motor)]

    step = 2 * params["axis_a"] / pieces
    radius = params["axis_a"] - excentricity + step
    while radius < params["axis_a"] + excentricity:
        radius2 = 2 * params["axis_a"] - radius
        point_pair = (focus1 - 0.5 * radius ** 2 * einf) ^ (focus2 - 0.5 * radius2 ** 2 * einf)
        point1, point2 = points_of_ipns_cra_point_pair(point_pair)
        points_of_ellipse.append(point1)
        points_of_ellipse.append(point2)
        radius += step
    circle_a = Idraw * ((center - 0.5 * params["axis_a"] ** 2 * einf) ^ e3)
    circle_b = Idraw * ((center - 0.5 * params["axis_b"] ** 2 * einf) ^ e3)
    axis_a = motor * Idraw * (e2 ^ e3) * ~motor
    axis_b = motor * Idraw * (e1 ^ e3) * ~motor
    return {"points": points_of_ellipse, "circles": [circle_a, circle_b], "axes": [axis_a, axis_b]}


def elements_of_hyperbola(hyperbola, pieces, max_radius):
    params = parameters_of_hyperbola(hyperbola)
    t = params["center_x"] * e1 + params["center_y"] * e2
    motor = translator_cra(t) * rotor_cra(params["theta"])
    excentricity = np.sqrt(params["axis_a"] ** 2 + params["axis_b"] ** 2)

    focus1 = corrected_point(motor * up(excentricity * e1) * ~motor)
    focus2 = corrected_point(motor * up(-excentricity * e1) * ~motor)
    points_of_hyperbola = [corrected_point(motor * up(-params["axis_a"] * e1) * ~motor),
                           corrected_point(motor * up(params["axis_a"] * e1) * ~motor)]

    radius = excentricity - params["axis_a"]
    step = (max_radius - radius) / pieces
    radius += step
    while radius < max_radius:
        radius2 = 2 * params["axis_a"] + radius
        point_pair = (focus1 - 0.5 * radius ** 2 * einf) ^ (focus2 - 0.5 * radius2 ** 2 * einf)
        point1, point2 = points_of_ipns_cra_point_pair(point_pair)
        points_of_hyperbola.append(point1)
        points_of_hyperbola.append(point2)
        point_pair = (focus2 - 0.5 * radius ** 2 * einf) ^ (focus1 - 0.5 * radius2 ** 2 * einf)
        point1, point2 = points_of_ipns_cra_point_pair(point_pair)
        points_of_hyperbola.append(point1)
        points_of_hyperbola.append(point2)
        radius += step
    asym1 = motor * Icra * (params["axis_b"] / params["axis_a"] * e1 + e2) * ~motor
    asym2 = motor * Icra * (-params["axis_b"] / params["axis_a"] * e1 + e2) * ~motor
    return {"points": points_of_hyperbola, "asymptotes": [asym1, asym2]}


def elements_of_parabola(parabola, pieces, length):
    params = parameters_of_parabola(parabola)
    motor = translator_cra(params["u"] * e1 + params["v"] * e2) * rotor_cra(params["theta"])
    points_of_parabola = [corrected_point(motor * up(0) * ~motor)]
    step = length / pieces
    i = step
    while i < length:
        y = i ** 2 / (2 * params["p"])
        points_of_parabola.append(corrected_point(motor * up(i * e1 + y * e2) * ~motor))
        points_of_parabola.append(corrected_point(motor * up(-i * e1 + y * e2) * ~motor))
        i += step

    return points_of_parabola


def add_conic_to_scene(scene, conic, color_conic):
    elements = elements_of_conic(conic)
    identification = identify_conic(conic)
    if identification == "hyperbola":
        scene.add_objects(elements["points"], color=color_conic)
        scene.add_objects(elements["asymptotes"], color=color_conic)
    elif identification == "parabola":
        return scene.add_objects(elements, color=color_conic)
    elif identification == "ellipse":
        scene.add_objects(elements["axes"], color=color_conic)
        scene.add_objects(elements["circles"], color=color_conic)
        scene.add_objects(elements["points"], color=color_conic)


def get_conic_by_points(points):
    points_gac = []
    points_spheres = []
    radius = 0.5
    for p in points:
        points_gac.append(init_point_gac(p.value[1], p.value[2]))
        points_spheres.append(p - 0.5 * radius ** 2 * einf)
    conic = get_conic_by_points_gac(points_gac)
    return conic, points_spheres


def get_conic_by_points_gac(points_gac):
    points = [x for x in points_gac]
    points.append(F0)
    points.append(G0)
    return np.matmul(I_GAC, wedge_of_n_vectors(points))


eo = eo
e1 = e1
e2 = e2
e3 = e3
einf = einf
e12 = e12
up = up

drawPlane = e3
Idraw = e1 ^ e2 ^ e3 ^ einf ^ eo
Icra = e1 ^ e2 ^ einf ^ eo
# jednicka
N = np.eye(4)

# pomocna matice pro inicializaci vektoru
N_ = np.eye(4)
N_[1, 1] = -1
N_[2, 2] = -1

# element = e1
# generatory CRA
E1 = e1 * N_
E2 = e2 * N_
Einf = einf * N_
E0 = eo * N_

Ep = 0.5 * Einf - E0
E_ = 0.5 * Einf + E0

# rozsireni na (4, 2)
Fp = np.zeros([4, 4])
Fp[0, 1] = 1
Fp[1, 0] = 1
Fp[-2, -1] = -1
Fp[-1, -2] = -1
F_ = np.zeros([4, 4])
F_[0, 1] = 1
F_[1, 0] = -1
F_[-2, -1] = -1
F_[-1, -2] = 1

Finf = F_ + Fp
F0 = 0.5 * (F_ - Fp)

# rozsireni na (5, 3)
Gp = np.zeros([4, 4])
Gp[0, 2] = 1
Gp[1, 3] = 1
Gp[2, 0] = 1
Gp[3, 1] = 1
G_ = np.zeros([4, 4])
G_[0, 2] = 1
G_[1, 3] = 1
G_[2, 0] = -1
G_[3, 1] = -1

Ginf = G_ + Gp
G0 = 0.5 * (G_ - Gp)

base_vectors = [E0, F0, G0, E1, E2, Einf, Finf, Ginf]
I_GAC = wedge_of_n_vectors(base_vectors)

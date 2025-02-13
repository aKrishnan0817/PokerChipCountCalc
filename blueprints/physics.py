from flask import Blueprint, render_template, request, redirect, send_file, url_for, send_from_directory
from PIL import Image
import os
import uuid
import numpy as np
from werkzeug.utils import secure_filename
import cv2
physics = Blueprint('physics', __name__)

@physics.route('/lightCone', methods=['GET', 'POST'])
def physics_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            image = Image.open(file)
            image.save('static/physics.png')
            return send_file('static/physics.png', as_attachment=True)
    return render_template('lightCone.html')





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in set(['png', 'jpg', 'jpeg', 'gif'])


def load_image(filepath):
    """
    Load an image using OpenCV, convert from BGR to RGB,
    and scale pixel values to the range [0,1].
    """
    img = cv2.imread(filepath, cv2.IMREAD_COLOR)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    return img


def save_image(image, filename):
    """
    Save an image (with pixel values in [0,1]) as a file.
    """
    img = np.clip(image * 255.0, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, img)


#############################
# Vectorized Transformation #
#############################

def compute_retarded_time(x, y, v, L, max_iter=10):
    """
    Solve for the retarded time t_r that satisfies:
        t_r + sqrt((x + v*t_r)**2 + y**2 + L**2) = 0.
    x and y are NumPy arrays.
    """
    t = -np.sqrt(x**2 + y**2 + L**2)
    for _ in range(max_iter):
        denom = np.sqrt((x + v * t)**2 + y**2 + L**2)
        f_val = t + denom
        f_deriv = 1 + (v * (x + v * t)) / denom
        t = t - f_val / f_deriv
    return t

def compute_projected_coordinates(x, y, v, t_r, L, f):
    """
    Using the retarded time, compute the observed (warped) coordinates.
    """
    X = x + v * t_r
    Y = y
    u = X * f / L
    w = Y * f / L
    return u, w, X, Y

def compute_doppler_shift(X, Y, L, v):
    """
    Calculate the Doppler shift factor for the light coming from (X, Y, 0).
    """
    r = np.sqrt(X**2 + Y**2 + L**2)
    cos_theta = X / r  # for motion along x.
    doppler = np.sqrt((1 + v * cos_theta) / (1 - v * cos_theta))
    return doppler

def adjust_color(image, doppler):
    """
    Adjust the RGB color based on the Doppler factor.
    Red is decreased (red-shift) and blue is increased (blue-shift) heuristically.
    """
    new_image = np.empty_like(image)
    new_image[..., 0] = np.clip(image[..., 0] / doppler, 0, 1)
    new_image[..., 1] = image[..., 1]
    new_image[..., 2] = np.clip(image[..., 2] * doppler, 0, 1)
    return new_image

def relativistic_transform(image, v=0.75, L=10.0, width_phys=2.0, height_phys=2.0, f=1.0):
    """
    Apply a simplified, vectorized relativistic transformation to an image.
    
    Parameters:
      image      : (H, W, 3) NumPy array with values in [0,1].
      v          : Speed (fraction of c).
      L          : Observer distance.
      width_phys : Physical width of the image plane.
      height_phys: Physical height of the image plane.
      f          : Focal length for projection.
      
    Returns:
      out_image  : Transformed image (same resolution as input).
      ranges     : Tuple (u_min, u_max, w_min, w_max) for projected coordinates.
    """
    H, W, _ = image.shape
    xs = np.linspace(-width_phys/2, width_phys/2, W)
    ys = np.linspace(-height_phys/2, height_phys/2, H)
    x_grid, y_grid = np.meshgrid(xs, ys)
    
    # Compute retarded time
    t_r = compute_retarded_time(x_grid, y_grid, v, L, max_iter=10)
    # Compute warped coordinates via projection
    u, w, X, Y = compute_projected_coordinates(x_grid, y_grid, v, t_r, L, f)
    # Compute Doppler shift factor and adjust color
    doppler = compute_doppler_shift(X, Y, L, v)
    new_image = adjust_color(image, doppler)
    
    # Map computed continuous coordinates to an output pixel grid.
    u_min, u_max = u.min(), u.max()
    w_min, w_max = w.min(), w.max()
    j_out = ((u - u_min) / (u_max - u_min) * (W - 1)).astype(np.int32)
    i_out = ((w - w_min) / (w_max - w_min) * (H - 1)).astype(np.int32)
    
    flat_indices = (i_out.ravel() * W) + j_out.ravel()
    flat_colors = new_image.reshape(-1, 3)
    num_pixels = H * W
    out_image_vec = np.zeros((num_pixels, 3), dtype=np.float32)
    for channel in range(3):
        out_image_vec[:, channel] = np.bincount(flat_indices,
                                                 weights=flat_colors[:, channel],
                                                 minlength=num_pixels)
    count = np.bincount(flat_indices, minlength=num_pixels)
    out_image = out_image_vec.reshape(H, W, 3)
    count = count.reshape(H, W)
    mask = count > 0
    out_image[mask] /= count[mask, None]
    
    return out_image, (u_min, u_max, w_min, w_max)


#########################
# Flask Routes & Views  #
#########################

@physics.route('/relativistic_image_transformation', methods=['GET', 'POST'])
def image_transform():
    # Default parameters for the form
    default_params = {
        "v": 0.99,
        "L": 20.0,
        "width_phys": 4.0,
        "height_phys": 4.0,
        "f": 1.0
    }
    result_image_url = None
    original_image_url = None

    explanation_text = """
    <p>This demonstration simulates the appearance of an image when viewed from a frame moving at relativistic speeds.
    The process involves:</p>
    <ul>
      <li><strong>Lorentz Contraction:</strong> Objects contract in the direction of motion.</li>
      <li><strong>Relativistic Aberration:</strong> Light is “bent” so that the apparent position of features is shifted.</li>
      <li><strong>Doppler Shift:</strong> Colors are shifted (blue-shifted when approaching, red-shifted when receding).</li>
      <li><strong>Light-Travel Time Delay:</strong> Different parts of the image are seen from different times, adding extra warping.</li>
    </ul>
    <p>Adjust the parameters below and upload your image to see the effect in action!</p>
    """
    
    if request.method == 'POST':
        try:
            v = float(request.form.get('v', default_params['v']))
            L = float(request.form.get('L', default_params['L']))
            width_phys = float(request.form.get('width_phys', default_params['width_phys']))
            height_phys = float(request.form.get('height_phys', default_params['height_phys']))
            f = float(request.form.get('f', default_params['f']))
        except:
            v, L, width_phys, height_phys, f = default_params.values()
        
        img = None
        # Process uploaded file if exists.
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                original_filename = str(uuid.uuid4()) + "_" + filename
                file_path = "uploads/" + original_filename
                file.save(file_path)
                img = load_image(file_path)
                # Set the original image URL for display.
                original_image_url = url_for('physics.uploaded_file', filename=original_filename)
            else:
                img = None
        
        if img is None:
            return render_template("relativeImageTransform.html", explanation=explanation_text, error="Image could not be loaded.", params=default_params)
        
        # Apply transformation.
        transformed, ranges = relativistic_transform(img, v=v, L=L, width_phys=width_phys, height_phys=height_phys, f=f)
        out_filename = "transformed_" + str(uuid.uuid4()) + ".png"
        out_filepath = "uploads/" + out_filename
        save_image(transformed, out_filepath)
        result_image_url = url_for('physics.uploaded_file', filename=out_filename)
        
        return render_template("relativeImageTransform.html", explanation=explanation_text, params=request.form, result_image_url=result_image_url, original_image_url=original_image_url)
    
    # For GET requests, use defaults.
    return render_template("relativeImageTransform.html", explanation=explanation_text, params=default_params, result_image_url=result_image_url, original_image_url=None)
@physics.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory("uploads/" , filename)



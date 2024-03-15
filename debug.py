from main import *
import cv2 as cv

def normalize_mask(mask, channel:int = None):
    if channel is not None:
        assert (len(mask.shape) == 3 and 0 <= channel < mask.shape[2]), \
            f"channel {channel} is out of bounds for mask with shape {mask.shape}"
        mask = mask[:,:,channel]
    assert (len(mask.shape) == 2) or (len(mask.shape) == 3 and mask.shape[2] == 1), \
        "mask must be 2D or 3D with 1 channel, or specify channel in bounds"
    if mask.dtype == bool:
        mask = (255*np.uint8(mask))
    elif (mask.dtype == float) or (mask.dtype == np.float64) or (mask.dtype == np.float32) or (mask.dtype == np.uint8):
        mask = np.uint8(255 * (mask / mask.max()))
    else:
        raise ValueError(f"mask has dtype {mask.dtype}")
    return mask


def show_mask(mask, channel:int = None):
    mask = normalize_mask(mask, channel)
    img = Image.fromarray(mask)
    img.show()


while True:
    img = Image.open("screenshot.png")
    np_img = np.array(img)[:,:,:-1]
    chat_box = select_chat_box(img)
    
    mask = extract_mask(None, np_img)
    evs = extract_chat_events(None, np_img, mask)
    print(evs)
    try:
        s = input("> ")
        eval(s)
    except Exception as e:
        print(e)

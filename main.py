import argparse
import os

import cv2
import imutils
import numpy as np
import pytesseract
from imutils.perspective import four_point_transform


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--image", type=str, required=True, help="path to input image"
    )
    args = parser.parse_args()

    # check if image with given path exists
    if not os.path.exists(args.image):
        raise Exception("The given image does not exist.")

    # load the image, resize and compute ratio
    img_orig = cv2.imread(args.image)
    image = img_orig.copy()
    image = imutils.resize(image, width=500)
    ratio = img_orig.shape[1] / float(image.shape[1])

    # convert the image to grayscale, blur it slightly, and then apply # edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("gray.jpg", gray)

    # Apply adaptive thresholding to filter out noise and enhance text visibility
    #image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 41)
    image = gray
    #cv2.imwrite("filtered.jpg", image)

    # Define a kernel for morphological operations (erosion and dilation)
    kernel = np.ones((1, 1), np.uint8)

    # Perform morphological opening to remove small noise regions
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    cv2.imwrite("opening.jpg", image)

    # Perform morphological closing to fill gaps in text regions
    closing = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    cv2.imwrite("closing.jpg", closing)


    ret1, th1 = cv2.threshold(gray, 88, 255, cv2.THRESH_BINARY)
    cv2.imwrite("th1.jpg", th1)
    #ret2, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #cv2.imwrite("th2.jpg", th2)
    #blurred = cv2.GaussianBlur(
    #    th2,
    #    (
    #        5,
    #        5,
    #    ),
    #    0,
    #)
    or_image = cv2.bitwise_or(th1, closing)
    cv2.imwrite("or.jpg", or_image)
    #cv2.imwrite("blurred.jpg", blurred)
    #ret3, th3 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #edged = cv2.Canny(th1, 75, 200)
    edged = or_image
    cv2.imwrite("edged.jpg", edged)

    # find contours in the edge map and sort them by size in descending
    # order
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # initialize a contour that corresponds to the receipt outline
    receiptCnt = None
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # if our approximated contour has four points, then we can
        # assume we have found the outline of the receipt
        if len(approx) == 4:
            receiptCnt = approx
            break

    # cv2.drawContours(image, [receiptCnt], -1, (0, 255, 0), 2)
    # cv2.imwrite('image_with_outline.jpg', image)
    # cv2.imshow("Receipt Outline", image)
    # cv2.waitKey(0)

    # if the receipt contour is empty then our script could not find the
    # outline and we should be notified
    if receiptCnt is None:
        raise Exception(
            (
                "Could not find receipt outline. "
                "Try debugging your edge detection and contour steps."
            )
        )

    # apply a four-point perspective transform to the *original* image to
    # obtain a top-down bird's-eye view of the receipt
    receipt = four_point_transform(img_orig, receiptCnt.reshape(4, 2) * ratio)
    # cv2.imwrite('transformed_receipt.jpg', receipt)

    # apply OCR to the receipt image by assuming column data, ensuring
    # the text is *concatenated across the row* (additionally, for your
    # own images you may need to apply additional processing to cleanup
    # the image, including resizing, thresholding, etc.)
    options = "--psm 6"
    text = pytesseract.image_to_string(
        cv2.cvtColor(receipt, cv2.COLOR_BGR2RGB), config=options
    )
    # show the raw output of the OCR process
    print("[INFO] raw output:")
    print("==================")
    print(text)
    print("\n")


if __name__ == "__main__":
    main()

import os
import argparse
import warnings
import subprocess

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import glob
import math
import numpy as np
import pandas as pd
from skimage import io
import matplotlib.pyplot as plt

import tensorflow as tf

keras = tf.keras
from keras import backend as K
from keras.models import Sequential
from keras import optimizers
from keras.layers import Dense, Activation, Dropout
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import *

from plot_keras_history import plot_history
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import classification_report
from sklearn.preprocessing import label_binarize
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from faker import Faker
from imgaug import augmenters as iaa

from Toolbox.Tools import *

# ------------------------------------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------------------------------------

def compute_class_weights(df, mu=0.15):
    """
    Compute class weights for the given dataframe.
    """
    # Compute the value counts for each class
    value_counts = df['Label'].value_counts().to_dict()
    total = sum(value_counts.values())
    keys = value_counts.keys()

    # To store the class weights
    class_weight = dict()

    # Compute the class weights for each class
    for key in keys:
        score = math.log(mu * total / float(value_counts[key]))
        class_weight[key] = score if score > 1.0 else 1.0

    return class_weight


def recall(y_true, y_pred):
    """
    Compute the recall metric.
    """
    # Compute the true positives
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    # Compute the possible positives
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    # Compute the recall
    r = true_positives / (possible_positives + K.epsilon())

    return r


def precision(y_true, y_pred):
    """
    Compute the precision metric.
    """
    # Compute the true positives
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    # Compute the predicted positives
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    # Compute the precision
    p = true_positives / (predicted_positives + K.epsilon())

    return p


def f1_score(y_true, y_pred):
    """
    Compute the F1-score metric.
    """
    # Compute precision and recall using the previously defined functions
    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)

    # Compute the F1-score
    f1 = 2 * (p * r) / (p + r + K.epsilon())

    return f1

# ------------------------------------------------------------------------------------------------------------------
# Training
# ------------------------------------------------------------------------------------------------------------------

def train_classifier(args):
    """

    """

    print(f"\n#########################################\n"
          f"Classifier\n"
          f"#########################################\n")

    # Check that the user has GPU available
    if tf.config.list_physical_devices('GPU'):
        print("NOTE: Found GPU")
    else:
        print("WARNING: No GPU found; defaulting to CPU")

    # ---------------------------------------------------------------------------------------
    # Source directory setup
    SOURCE_DIR = f"{args.output_dir}/"

    # Run Name
    RUN = Faker().name().replace(" ", "_").replace(".", "")

    # We'll also create folders in this source to hold results of the model
    MODEL_DIR = SOURCE_DIR + f"model/{RUN}/"
    WEIGHTS_DIR = MODEL_DIR + "weights/"
    LOGS_DIR = MODEL_DIR + "logs/"

    # Make the directories
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    print(f"NOTE: Model Run - {RUN}")
    print(f"NOTE: Model Directory - {MODEL_DIR}")
    print(f"NOTE: Log Directory - {LOGS_DIR}")

    # ---------------------------------------------------------------------------------------
    # Data setup
    print(f"\n#########################################\n"
          f"Creating Datasets\n"
          f"#########################################\n")

    # If the user provides multiple patch dataframes
    patches_df = pd.DataFrame()

    for patches in args.patches:
        if os.path.exists(patches):
            # Patch dataframe
            patches = pd.read_csv(patches)
            patches = patches.dropna()
            patches_df = pd.concat((patches_df, patches))
        else:
            raise Exception(f"ERROR: Patches dataframe {patches} does not exist")

    # Names of all images; sets to be split based on images
    image_names = patches_df['Image Name'].unique()

    # Split the Images into training, validation, and test sets.
    # We split based on the image names, so that we don't have the same image in multiple sets.
    training_images, testing_images = train_test_split(image_names, test_size=0.35, random_state=42)
    validation_images, testing_images = train_test_split(testing_images, test_size=0.5, random_state=42)

    # Create training, validation, and test dataframes
    train_df = patches_df[patches_df['Image Name'].isin(training_images)]
    valid_df = patches_df[patches_df['Image Name'].isin(validation_images)]
    test_df = patches_df[patches_df['Image Name'].isin(testing_images)]

    # If there isn't one class sample in each train and valid sets
    # Keras will throw an error; hacky way of fixing this.
    if len(set(train_df['Label'].unique())) - len(set(valid_df['Label'].unique())):
        print("NOTE: Sampling one of each class category")
        # Holds one sample of each class category
        sample = pd.DataFrame()
        # Gets one sample from patches_df
        for label in patches_df['Label'].unique():
            one_sample = patches_df[patches_df['Label'] == label].sample(n=1)
            sample = pd.concat((sample, one_sample))

        train_df = pd.concat((sample, train_df))
        valid_df = pd.concat((sample, valid_df))
        test_df = pd.concat((sample, test_df))

    train_df.reset_index(drop=True, inplace=True)
    valid_df.reset_index(drop=True, inplace=True)
    test_df.reset_index(drop=True, inplace=True)

    # The number of class categories
    class_names = train_df['Label'].unique().tolist()
    num_classes = len(class_names)
    print(f"NOTE: Number of classes in training set is {len(train_df['Label'].unique())}")
    print(f"NOTE: Number of classes in validation set is {len(valid_df['Label'].unique())}")
    print(f"NOTE: Number of classes in testing set is {len(test_df['Label'].unique())}")

    # ------------------------------------------------------------------------------------------------------------------
    # Data Exploration
    plt.figure(figsize=(10, 5))

    # Set the same y-axis limits for all subplots
    ymin = 0
    ymax = train_df['Label'].value_counts().max() + 10

    # Plotting the train data
    plt.subplot(1, 3, 1)
    plt.title(f"Train: {len(train_df)} Classes: {len(train_df['Label'].unique())}")
    ax = train_df['Label'].value_counts().plot(kind='bar')
    ax.set_ylim([ymin, ymax])

    # Plotting the valid data
    plt.subplot(1, 3, 2)
    plt.title(f"Valid: {len(valid_df)} Classes: {len(valid_df['Label'].unique())}")
    ax = valid_df['Label'].value_counts().plot(kind='bar')
    ax.set_ylim([ymin, ymax])

    # Plotting the test data
    plt.subplot(1, 3, 3)
    plt.title(f"Test: {len(test_df)} Classes: {len(test_df['Label'].unique())}")
    ax = test_df['Label'].value_counts().plot(kind='bar')
    ax.set_ylim([ymin, ymax])

    # Saving and displaying the figure
    plt.savefig(LOGS_DIR + "DatasetSplit.png")
    plt.show()

    if os.path.exists(LOGS_DIR + "DatasetSplit.png"):
        print(f"NOTE: Datasplit Figure saved in {LOGS_DIR}")

    # ------------------------------------------------------------------------------------------------------------------
    # Start of parameter setting
    print(f"\n#########################################\n"
          f"Setting Parameters\n"
          f"#########################################\n")

    # Calculate weights
    if args.weighted_loss:
        print(f"NOTE: Calculating weights for weighted loss function")
        class_weight = compute_class_weights(train_df)
    else:
        class_weight = {c: 1.0 for c in range(num_classes)}

    # Reformat for model.fit()
    class_weight = {i: list(class_weight.values())[i] for i in range(len(list(class_weight.values())))}

    # ------------------------------------------------------------------------------------------------------------------
    # Data Augmentation
    dropout_rate = args.dropout_rate

    # For the validation and testing sets
    augs_for_valid = iaa.Sequential([iaa.Resize(224, interpolation='linear')])

    # For the training set, if selected
    if args.augment_data:
        print(f"NOTE: Augmenting Training Dataset")
        augs_for_train = iaa.Sequential([
            iaa.Resize(224, interpolation='linear'),
            iaa.Fliplr(0.5),
            iaa.Flipud(0.5),
            iaa.Rot90([1, 2, 3, 4], True),
            iaa.Sometimes(.3, iaa.Affine(scale=(.95, 1.05))),
        ])
    else:
        augs_for_train = augs_for_valid

    # ------------------------------------------------------------------------------------------------------------------
    # Training Parameters
    num_epochs = args.num_epochs

    # Batch size is dependent on the amount of memory available on your machine
    batch_size = args.batch_size

    # Defines the length of an epoch, all images are used
    steps_per_epoch_train = len(train_df) / batch_size
    steps_per_epoch_valid = len(valid_df) / batch_size

    # Learning rate
    lr = args.learning_rate

    # Training images are augmented, and then normalized
    train_augmentor = ImageDataGenerator(preprocessing_function=augs_for_train.augment_image)

    # Reading from dataframe
    train_generator = train_augmentor.flow_from_dataframe(dataframe=train_df,
                                                          directory=None,
                                                          x_col='Path',
                                                          y_col='Label',
                                                          target_size=(224, 224),
                                                          color_mode="rgb",
                                                          class_mode='categorical',
                                                          batch_size=batch_size,
                                                          shuffle=True,
                                                          seed=42)

    # Only normalize images, no augmentation
    validate_augmentor = ImageDataGenerator(preprocessing_function=augs_for_valid.augment_image)

    # Reading from dataframe
    validation_generator = validate_augmentor.flow_from_dataframe(dataframe=valid_df,
                                                                  directory=None,
                                                                  x_col='Path',
                                                                  y_col='Label',
                                                                  target_size=(224, 224),
                                                                  color_mode="rgb",
                                                                  class_mode='categorical',
                                                                  batch_size=batch_size,
                                                                  shuffle=True,
                                                                  seed=42)

    # Count the occurrences of each label
    label_counts = test_df['Label'].value_counts()

    # Sort the DataFrame based on label counts in descending order
    test_df = test_df.sort_values(by='Label', key=lambda x: x.map(label_counts), ascending=False)

    # Create the generator
    test_augmentor = ImageDataGenerator(preprocessing_function=augs_for_valid.augment_image)

    # Reading from dataframe
    test_generator = test_augmentor.flow_from_dataframe(dataframe=test_df,
                                                        x_col='Path',
                                                        y_col='Label',
                                                        target_size=(224, 224),
                                                        color_mode="rgb",
                                                        class_mode='categorical',
                                                        batch_size=batch_size,
                                                        shuffle=False,
                                                        seed=42)

    # ------------------------------------------------------------------------------------------------------------------
    # Building Model
    print(f"\n#########################################\n"
          f"Building Model\n"
          f"#########################################\n")

    convnet = getattr(keras.applications, args.model_name)(
        include_top=False,
        include_preprocessing=True,
        weights='imagenet',
        input_shape=(224, 224, 3),
        pooling='max',
        classes=num_classes,
        classifier_activation='softmax',
    )

    # Here we create the entire model, with the convnet previously defined
    # as the encoder. Our entire model is simple, consisting of the convnet,
    # a dropout layer for regularization, and a fully-connected layer with
    # softmax activation for classification.
    model = Sequential([
        convnet,
        Dropout(dropout_rate),
        Dense(num_classes),
        Activation('softmax')
    ])

    # Display model to user
    graph = model.summary()
    print(f"\n{graph}\n")

    # ------------------------------------------------------------------------------------------------------------------
    # Callbacks
    callbacks = [
        ReduceLROnPlateau(monitor='val_loss',
                          factor=.65,
                          patience=3,
                          verbose=1),

        ModelCheckpoint(filepath=WEIGHTS_DIR + "model-{epoch:03d}-{acc:03f}-{val_acc:03f}.h5",
                        monitor='val_loss',
                        save_weights_only=False,
                        save_best_only=True,
                        verbose=1),

        EarlyStopping(monitor="val_loss",
                      min_delta=0,
                      patience=10,
                      verbose=1,
                      mode="auto",
                      baseline=None,
                      restore_best_weights=True),

        TensorBoard(log_dir=LOGS_DIR, histogram_freq=0),
    ]

    # ------------------------------------------------------------------------------------------------------------------
    # Compile model
    model.compile(loss=args.loss_function,
                  optimizer=optimizers.Adam(learning_rate=lr),
                  metrics=['acc', precision, recall, f1_score])

    # ------------------------------------------------------------------------------------------------------------------
    # Display Tensorboard
    if args.tensorboard:
        try:
            print(f"\n#########################################\n"
                  f"Tensorboard\n"
                  f"#########################################\n")

            # Call Tensorboard using the environment's python exe
            tensorboard_exe = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'tensorboard')
            process = subprocess.Popen([tensorboard_exe, "--logdir", LOGS_DIR])

            # Let it load
            time.sleep(15)

        except Exception as e:
            print(f"WARNING: Could not open TensorBoard; check that it is installed\n{e}")

    # ------------------------------------------------------------------------------------------------------------------
    # Train Model

    try:

        print(f"\n#########################################\n"
              f"Training\n"
              f"#########################################\n")

        print("NOTE: Starting Training")
        history = model.fit(train_generator,
                            steps_per_epoch=steps_per_epoch_train,
                            epochs=num_epochs,
                            validation_data=validation_generator,
                            validation_steps=steps_per_epoch_valid,
                            callbacks=callbacks,
                            verbose=1,
                            class_weight=class_weight)
    except Exception as e:
        print(f"ERROR: There was an issue with training!\n"
              f"Read the 'Error.txt file' in the Logs Directory")

        # Write the error to text file
        with open(f"{LOGS_DIR}Error.txt", 'a') as file:
            file.write(f"Caught exception: {str(e)}\n")

        # Exit early
        sys.exit(1)

    # ------------------------------------------------------------------------------------------------------------------
    # Plot and save results
    plot_history(history, single_graphs=True, path=f"{LOGS_DIR}");
    print(f"NOTE: Training History Figure saved in {LOGS_DIR}")

    # ------------------------------------------------------------------------------------------------------------------
    # Test Dataset
    print(f"\n#########################################\n"
          f"Validating with Test Dataset\n"
          f"#########################################\n")

    # Get the best weights
    weights = sorted(glob.glob(WEIGHTS_DIR + "*.h5"), key=os.path.getmtime)
    best_weights = weights[-1]

    # Load into the model
    model.load_weights(best_weights)
    print(f"NOTE: Loaded best weights {best_weights}")

    # ------------------------------------------------------------------------------------------------------------------
    # Make predictions on test set
    probabilities = model.predict_generator(test_generator)

    # Collapse the probability distribution to the most likely category
    predictions = np.argmax(probabilities, axis=1)

    # ------------------------------------------------------------------------------------------------------------------
    # Create classification report
    report = classification_report(test_generator.classes,
                                   predictions,
                                   target_names=test_generator.class_indices.keys())

    # Save the report to a file
    with open(f"{LOGS_DIR}Classification_Report.txt", "w") as file:
        file.write(report)
    print(f"NOTE: Classification Report saved in {LOGS_DIR}")

    # --- Confusion Matrix
    # Calculate the overall accuracy
    overall_accuracy = accuracy_score(test_generator.classes, predictions)
    # Calculate the number of samples
    num_samples = len(test_generator.classes)
    # Convert the accuracy and number of samples to strings
    accuracy_str = f"{overall_accuracy:.2f}"
    num_samples_str = str(num_samples)

    # Calculate the confusion matrix and normalize it
    cm = confusion_matrix(test_generator.classes, predictions)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    cm_normalized = np.round(cm_normalized, decimals=2)

    # Get the sum of each row (number of samples per class)
    row_sums = cm.sum(axis=1)

    # Sort the confusion matrix and row sums in descending order
    sort_indices = np.argsort(row_sums)[::-1]
    cm_sorted = cm_normalized[sort_indices][:, sort_indices]
    class_labels_sorted = np.array(list(test_generator.class_indices.keys()))[sort_indices]

    # Create the display
    disp = ConfusionMatrixDisplay(confusion_matrix=cm_sorted, display_labels=class_labels_sorted)
    # Set the figure size
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_title(f"Confusion Matrix\nOverall Accuracy: {accuracy_str}, Samples: {num_samples_str}")
    # Plot the confusion matrix
    disp.plot(ax=ax, cmap=plt.cm.Blues, values_format='g')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    plt.savefig(f"{LOGS_DIR}Confusion_Matrix.png")
    plt.show()

    print(f"NOTE: Confusion Matrix saved in {LOGS_DIR}")

    # --- ROC
    # Convert the true labels to binary format
    binary_true_labels = label_binarize(test_generator.classes, classes=np.arange(num_classes))

    # Create a dict for the legend
    class_indices = {int(v): k for k, v in test_generator.class_indices.items()}

    # Compute the false positive rate (FPR), true positive rate (TPR), and AUC for each class
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    for i in range(num_classes):
        fpr[i], tpr[i], _ = roc_curve(binary_true_labels[:, i], probabilities[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # Plot the ROC curves for each class
    plt.figure(figsize=(10, 10))
    for i in range(num_classes):
        roc_val = np.around(roc_auc[i], 2)
        plt.plot(fpr[i], tpr[i], lw=2, label=f'{class_indices[i]} AUC = {roc_val}')

    # Plot the random guessing line
    plt.plot([0, 1], [0, 1], color='black', lw=1, linestyle='--')

    # Set plot properties
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.xlabel('False Positive Rate (FPR)')
    plt.ylabel('True Positive Rate (TPR)')
    plt.title('Receiver Operating Characteristic (ROC) Curves')
    plt.legend(loc='lower right', title='Classes')
    plt.savefig(LOGS_DIR + "ROC_Curves.png")
    plt.show()

    print(f"NOTE: ROC Figure saved in {LOGS_DIR}")

    # --- Threshold
    # Higher values represent more sure/confident predictions
    # .1 unsure -> .5 pretty sure -> .9 very sure

    # Creating a graph of the threshold values and the accuracy
    threshold_values = np.arange(0.0, 1.0, 0.05)
    class_ACC = []
    sure_percentage = []

    # Looping through the threshold values and calculating the accuracy and percentage
    for threshold in threshold_values:
        # Creating a list to store the sure index
        sure_index = []
        # Looping through all predictions and calculating the sure predictions
        for i in range(0, len(probabilities)):
            # If the difference between the most probable class and the second most probable class
            # is greater than the threshold, add it to the sure index
            if (sorted(probabilities[i])[-1]) - (sorted(probabilities[i])[-2]) > threshold:
                sure_index.append(i)

        # Calculating the accuracy for the threshold value
        sure_test_y = np.take(test_generator.classes, sure_index, axis=0)
        sure_pred_y = np.take(predictions, sure_index)
        sure_percentage.append(len(sure_index) / len(probabilities))
        class_ACC.append(accuracy_score(sure_test_y, sure_pred_y))

    # Plotting the results
    plt.figure(figsize=(10, 5))
    plt.plot(threshold_values, class_ACC)
    plt.plot(threshold_values, sure_percentage, color='gray', linestyle='--')
    plt.xlabel('Threshold Values')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.xticks(ticks=np.arange(0, 1.05, 0.1))
    plt.ylabel('Classification Accuracy / Sure Percentage')
    plt.title('Identifying the ideal threshold value')
    plt.legend(['Classification Accuracy', 'Sure Percentage'])
    plt.savefig(LOGS_DIR + "AccuracyThreshold.png")
    plt.show()

    print(f"NOTE: Threshold Figure saved in {LOGS_DIR}")

    # ------------------------------------------------------------------------------------------------------------------
    # Save the best model
    model.save(f"{MODEL_DIR}Best_Model_and_Weights.h5")
    print(f"NOTE: Best Model and Weights saved in {MODEL_DIR}")

    if args.tensorboard:
        # Close Tensorboard
        process.terminate()


def main():
    parser = argparse.ArgumentParser(description='Train an Image Classifier')

    parser.add_argument('--patches', required=True, nargs="+",
                        help='The path to the patch labels csv file output the Patches tool')

    parser.add_argument('--model_name', type=str, default='EfficientNetV2B0',
                        help='The convolutional encoder to fine-tune; pretrained on Imagenet')

    parser.add_argument('--loss_function', type=str, default='categorical_crossentropy',
                        help='The loss function to use to train the model')

    parser.add_argument('--weighted_loss', type=bool, default=True,
                        help='Use a weighted loss function; good for imbalanced datasets')

    parser.add_argument('--augment_data', type=bool, default=True,
                        help='Apply affine augmentations to training data')

    parser.add_argument('--dropout_rate', type=float, default=0.5,
                        help='Amount of dropout in model (augmentation)')

    parser.add_argument('--num_epochs', type=int, default=1,
                        help='Starting learning rate')

    parser.add_argument('--batch_size', type=int, default=64,
                        help='Starting learning rate')

    parser.add_argument('--learning_rate', type=float, default=0.0001,
                        help='Starting learning rate')

    parser.add_argument('--tensorboard', type=bool, default=True,
                        help='Display training on Tensorboard')

    parser.add_argument('--output_dir', type=str, required=True,
                        help='Directory to save updated label csv file.')

    args = parser.parse_args()

    try:
        train_classifier(args)
        print('Done.')

    except Exception as e:
        print(f'ERROR: Could not finish successfully.{e}')


if __name__ == '__main__':
    main()

import os.path

from CoralNet import *


# -------------------------------------------------------------------------------------------------
# Functions for downloading all of CoralNet
# -------------------------------------------------------------------------------------------------

def download_coralnet_labelsets(driver, output_dir=None):
    """
    Download a list of all labelsets in CoralNet.
    """

    # Variable to hold the list of sources
    labelset = None

    # Go to the images page
    driver.get(CORALNET_LABELSET_URL)

    print("NOTE: Downloading CoralNet Labelset List")

    try:
        # Parse the HTML response using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Get the table with all labelset information
        table = soup.find_all('tr', attrs={"data-label-id": True})

        # Loop through each row, grab the information, store in lists
        rows = []
        for row in tqdm(table):
            # Grab attributes from row
            attributes = row.find_all("td")
            # Extract each attribute, store in variable
            name = attributes[0].text
            label_id = attributes[0].find("a").get("href").split("/")[2]
            url = CORALNET_URL + attributes[0].find("a").get("href")
            functional_group = attributes[1].text
            popularity = attributes[2].find("div").get("title").split("%")[0]
            short_code = attributes[4].text
            # Additional attribute information
            is_duplicate = False
            is_verified = False
            has_calcification = False
            notes = ""

            # Loop through the optional attributes
            for column in attributes[3].find_all("img"):
                if column.get("alt") == "Duplicate":
                    is_duplicate = True
                    notes = column.get("title")
                if column.get("alt") == "Verified":
                    is_verified = True
                if column.get("alt") == "Has calcification rate data":
                    has_calcification = True

            rows.append([label_id,
                         name,
                         url,
                         functional_group,
                         popularity,
                         short_code,
                         is_duplicate,
                         notes,
                         is_verified,
                         has_calcification])

        # Create dataframe
        labelset = pd.DataFrame(rows, columns=['Label ID',
                                               'Name',
                                               'URL',
                                               'Functional Group',
                                               'Popularity %',
                                               'Short Code',
                                               'Duplicate',
                                               'Duplicate_Notes',
                                               'Verified',
                                               'Has Calcification Rates'])

        # See if the user wants to save locally
        if output_dir:

            # Save locally
            labelset.to_csv(f"{output_dir}CoralNet_Labelset_List.csv")

            # Check that it was saved
            if os.path.exists(f"{output_dir}CoralNet_Labelset_List.csv"):
                print("NOTE: Labelset list saved successfully")
            else:
                raise Exception("ERROR: Could not download Labelset list; "
                                "check that variable Labelset URL is correct.")

    except Exception as e:
        print(f"Error: Unable to get labelset list from CoralNet.\n{e}")
        labelset = None

    return driver, labelset


def download_coralnet_sources(driver, output_dir=None):
    """
    Downloads a list of all the public sources currently on CoralNet.
    """

    # Variable to hold the list of sources
    sources = None

    # Go to the images page
    driver.get(CORALNET_SOURCE_URL)

    print("NOTE: Downloading CoralNet Source List")

    try:
        # Parse the HTML response using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all the instances of sources
        links = soup.find_all('ul', class_='object_list')[0].find_all("li")

        # Lists to store the source IDs and names
        source_urls = []
        source_ids = []
        source_names = []

        # Now, get all the source IDs and names on the page
        for link in tqdm(links):
            # Parse the information
            url = CORALNET_URL + link.find("a").get("href")
            source_id = url.split("/")[-2]
            source_name = link.find("a").text.strip()

            # Check what is grabbed it actually a source
            if source_id.isnumeric():
                source_urls.append(url)
                source_ids.append(source_id)
                source_names.append(source_name)

        # Store as a dict
        sources = {'Source_ID': source_ids,
                   'Source_Name': source_names,
                   'Source_URL': source_urls}

        # Create a dataframe
        sources = pd.DataFrame(sources)

        # Check if user wants to save locally:
        if output_dir:

            # Save locally
            sources.to_csv(f"{output_dir}CoralNet_Source_ID_List.csv")

            # Check that it was saved
            if os.path.exists(f"{output_dir}CoralNet_Source_ID_List.csv"):
                print("NOTE: CoralNet Source list saved successfully")
            else:
                raise Exception("ERROR: Could not download Source ID list; "
                                "check that variable CoralNet URL is correct.")
    except Exception as e:
        print(f"Error: Unable to get source list from CoralNet.\n{e}")
        sources = None

    return driver, sources


def get_sources_with(driver, labelsets, output_dir=None):
    """
    Downloads a list of sources that contain the specified labelsets.
    """

    # Go to the images page
    driver.get(CORALNET_LABELSET_URL)

    print("NOTE: Downloading list of sources")

    try:
        source_list = []

        # Loop through all labelset URLs
        for i, r in tqdm(labelsets.iterrows()):

            # Go to the labeset page
            driver.get(r['URL'])

            # Parse the HTML response using BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find all the source ids on the page
            a_tags = soup.find_all('a')
            for a_tag in a_tags:

                # It's an a_tag, but not one of interest
                if not '/source/' in a_tag.get('href'):
                    continue

                # Get the source id
                source_id = a_tag.get("href").split("/")[-2]
                source_id = source_id if source_id.isnumeric() else None
                # Get the URL
                source_url = f"{CORALNET_URL}/label/{source_id}/"
                # Get the source name
                source_name = a_tag.text.strip()

                # Add to the list if it's a valid source
                if source_id:
                    source_list.append([source_id,
                                        source_name,
                                        source_url,
                                        r['Name']])

        # If the list of source ids is not empty, save locally
        if source_list:

            # Convert to dataframe
            source_list = pd.DataFrame(source_list, columns=['Source_ID',
                                                             'Source_Name',
                                                             'Source_URL',
                                                             'Contains'])
            # Check to see if use wants to save locally
            if output_dir:

                # Save locally
                source_list.to_csv(f"{output_dir}Desired_Source_ID_List.csv")

                # Check that it exists
                if os.path.exists(f"{output_dir}Desired_Source_ID_List.csv"):
                    print("NOTE: Source ID List saved successfully")
                else:
                    raise Exception("ERROR: Could not save Source ID List")
        else:
            raise Exception("ERROR: No sources found")

    except Exception as e:
        print(f"ERROR: Unable to get list of Source IDs\n{e}")
        source_list = None

    return driver, source_list


# -------------------------------------------------------------------------------------------------
# Functions for downloading data from individual sources
# -------------------------------------------------------------------------------------------------

def download_metadata(driver, source_id, source_dir=None):
    """
    Given a source ID, download the labelset.
    """

    # To hold the metadata
    meta = []

    # Go to the meta page
    driver.get(CORALNET_URL + f"/source/{source_id}/")

    # First check that this is existing source the user has access to
    try:
        # Check the permissions
        driver, status = check_permissions(driver)

        # Check the status
        if "Page could not be found" in status.text or "don't have permission" in status.text:
            raise Exception(status.text.split('.')[0])

    except Exception as e:
        print(f"ERROR: {e} or you do not have permission to access it")
        sys.exit(1)

    print(f"NOTE: Downloading model metadata for {source_id}")

    try:
        # Convert the page to soup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        script = None

        # Of the scripts, find the one containing model metadata
        for script in soup.find_all("script"):
            if "Classifier overview" in script.text:
                script = script.text
                break

        # If the page doesn't have model metadata, then return None early
        if not script:
            raise Exception("NOTE: No model metadata found")

        # Parse the data when represented as a string, convert to dict
        data = script[script.find("data:"):].split(",\n")[0]
        data = eval(data[data.find("[{"):])

        # Loop through and collect meta from each model instance, store
        for point in tqdm(data):
            classifier_nbr = point["x"]
            score = point["y"]
            nimages = point["nimages"]
            traintime = point["traintime"]
            date = point["date"]
            source_id = point["pk"]

            meta.append([classifier_nbr,
                         score,
                         nimages,
                         traintime,
                         date,
                         source_id])

        # Convert list to dataframe
        meta = pd.DataFrame(meta, columns=['Classifier nbr',
                                           'Accuracy %',
                                           'N_Images',
                                           'Train_Time',
                                           'Date',
                                           'Model_ID'])

        if source_dir:
            # Save the metadata
            meta.to_csv(source_dir + "metadata.csv")

            # Check that it was saved
            if os.path.exists(source_dir + "metadata.csv"):
                print("NOTE: Metadata saved successfully")

    except Exception as e:
        print(f"ERROR: Issue with downloading metadata")
        meta = None

    return driver, meta


def download_labelset(driver, source_id, source_dir):
    """
    Given a source ID, download the labelset.
    """

    # To hold the labelset
    labelset = None

    # Go to the images page
    driver.get(CORALNET_URL + f"/source/{source_id}/labelset/")

    # First check that this is existing source the user has access to
    try:
        # Check the permissions
        driver, status = check_permissions(driver)

        # Check the status
        if "Page could not be found" in status.text or "don't have permission" in status.text:
            raise Exception(status.text.split('.')[0])

    except Exception as e:
        print(f"ERROR: {e} or you do not have permission to access it")
        sys.exit(1)

    print(f"NOTE: Downloading labelset for {source_id}")

    try:
        # Find the "Export Label to CSV" button
        path = 'input[type="submit"][value="Export label entries to CSV"]'
        button = driver.find_element(By.CSS_SELECTOR, path)

        # Click the button
        if button.is_enabled():
            button.click()
        else:
            raise Exception("ERROR: Button is not enabled")

        # Wait for the file to download
        while not os.path.exists(source_dir + "labelset.csv"):
            time.sleep(1)

        print("NOTE: Labelset saved successfully")
        labelset = pd.read_csv(source_dir + "labelset.csv")

    except Exception as e:
        print(f"ERROR: Issue with downloading labelset")
        labelset = None

    return driver, labelset


def download_image(image_url, image_path):
    """
    Download an image from a URL and save it to a directory. Return the path
    to the downloaded image if download was successful, otherwise return None.
    """

    # Do not re-download images that already exist
    if os.path.exists(image_path):
        return image_path, True

    # Send a GET request to the image URL
    response = requests.get(image_url)

    # Check if the response was successful
    if response.status_code == 200:
        # Save the image to the specified path
        with open(image_path, 'wb') as f:
            f.write(response.content)
        return image_path, True
    else:
        return image_path, False


def download_images(dataframe, source_dir):
    """
    Download images from URLs in a pandas dataframe and save them to a
    directory.
    """

    # Save the dataframe of images locally
    csv_file = source_dir + "images.csv"
    dataframe.to_csv(csv_file)
    # Check if the CSV file was saved before trying to download
    if os.path.exists(csv_file):
        print(f"NOTE: Saved image dataframe as CSV file")
    else:
        raise Exception("Error: Unable to save image CSV file")

    # Create the image directory if it doesn't exist
    image_dir = source_dir + "images/"
    os.makedirs(image_dir, exist_ok=True)

    print(f"NOTE: Downloading {len(dataframe)} images")

    # To hold the expired images
    expired_images = []

    with tqdm(total=len(dataframe)) as pbar:
        with concurrent.futures.ThreadPoolExecutor() as executor:

            results = []

            for index, row in dataframe.iterrows():
                # Get the image name and URL from the dataframe
                name = row['image_name']
                url = row['image_url']
                path = image_dir + name
                # Add the download task to the executor
                results.append(executor.submit(download_image, url, path))

            # Wait for all tasks to complete and collect the results
            for result in concurrent.futures.as_completed(results):
                # Get the downloaded image path
                downloaded_image_path, downloaded = result.result()
                # Get the image name from the downloaded image path
                basename = os.path.basename(downloaded_image_path)
                if not downloaded:
                    expired_images.append(basename)
                # Update the progress bar
                pbar.update(1)

    if expired_images:
        print(f"NOTE: {len(expired_images)} images had expired before being downloaded")
        print(f"NOTE: Saving list of expired images to {source_dir}expired_images.csv")
        expired_images = pd.DataFrame(expired_images, columns=['image_path'])
        expired_images.to_csv(source_dir + "expired_images.csv")


def get_image_url(session, image_page_url):
    """
    Given an image page URL, retrieve the image URL.
    """

    try:
        # Make a GET request to the image page URL using the authenticated session
        response = session.get(image_page_url)
        cookies = response.cookies

        # Convert the webpage to soup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the div element with id="original_image_container" and style="display:none;"
        image_container = soup.find('div', id='original_image_container', style='display:none;')

        # Find the img element within the div and get the src attribute
        image_url = image_container.find('img').get('src')

        return image_url

    except Exception as e:
        print(f"Error: Unable to get image URL from image page: {e}")
        return None


def get_image_urls(driver, image_page_urls):
    """
    Given a list of image page URLs, retrieve the image URLs for each image page.
    This function uses requests to authenticate with the website and retrieve
    the image URLs, because it is thread-safe, unlike Selenium.
    """

    print("NOTE: Retrieving image URLs")

    # List to hold all the image URLs
    image_urls = []

    # Send a GET request to the login page to retrieve the login form
    response = requests.get(LOGIN_URL)

    # Pass along the cookies
    cookies = response.cookies

    # Parse the HTML of the response using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the CSRF token from the HTML of the login page
    csrf_token = soup.find("input", attrs={"name": "csrfmiddlewaretoken"})

    # Create a dictionary with the login form fields and their values
    # (replace "username" and "password" with your actual username and
    # password)
    data = {
        "username": driver.capabilities['credentials']['username'],
        "password": driver.capabilities['credentials']['password'],
        "csrfmiddlewaretoken": csrf_token["value"],
    }

    # Include the "Referer" header in the request
    headers = {
        "Referer": LOGIN_URL,
    }

    # Use requests.Session to create a session that will maintain your login state
    session = requests.Session()

    # Use session.post() to submit the login form
    session.post(LOGIN_URL, data=data, headers=headers, cookies=cookies)

    with tqdm(total=len(image_page_urls)) as pbar:
        with ThreadPoolExecutor() as executor:
            # Submit the image_url retrieval tasks to the thread pool
            future_to_url = {executor.submit(get_image_url, session, url):
                                 url for url in image_page_urls}

            # Retrieve the completed results as they become available
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    image_url = future.result()
                    if image_url:
                        image_urls.append(image_url)
                except Exception as e:
                    print(f"ERROR: issue retrieving image URL for {url}\n{e}")
                finally:
                    pbar.update(1)
                    pbar.refresh()

    print(f"NOTE: Retrieved {len(image_urls)} image URLs")

    return driver, image_urls


def get_images(driver, source_id):
    """
    Given a source ID, retrieve the image names, and page URLs.
    """

    # To hold the images
    images = None

    # Go to the images page
    driver.get(CORALNET_URL + f"/source/{source_id}/browse/images/")

    # First check that this is existing source the user has access to
    try:
        # Check the permissions
        driver, status = check_permissions(driver)

        # Check the status
        if "Page could not be found" in status.text or "don't have permission" in status.text:
            raise Exception(status.text.split('.')[0])

    except Exception as e:
        print(f"ERROR: {e} or you do not have permission to access it")
        sys.exit(1)

    print(f"NOTE: Crawling all pages for source {source_id}")

    # Create lists to store the URLs and titles
    image_page_urls = []
    image_names = []

    try:
        # Find the element with the page number
        page_element = driver.find_element(By.CSS_SELECTOR, 'div.line')
        num_pages = int(page_element.text.split(" ")[-1]) // 20 + 1

        with tqdm(total=num_pages) as pbar:

            while True:

                # Find all the image elements
                url_elements = driver.find_elements(By.CSS_SELECTOR, '.thumb_wrapper a')
                name_elements = driver.find_elements(By.CSS_SELECTOR, '.thumb_wrapper img')

                # Iterate over the image elements
                for url_element, name_element in list(zip(url_elements, name_elements)):
                    # Extract the href attribute (URL)
                    image_page_url = url_element.get_attribute('href')
                    image_page_urls.append(image_page_url)

                    # Extract the title attribute (image name)
                    image_name = name_element.get_attribute('title').split(" - ")[0]
                    image_names.append(image_name)

                path = 'input[title="Next page"]'
                next_button = driver.find_elements(By.CSS_SELECTOR, path)

                if next_button:
                    next_button[0].click()
                    pbar.update(1)
                    pbar.refresh()

                else:
                    print("NOTE: Finished crawling all pages")
                    break

            images = pd.DataFrame({'image_page': image_page_urls,
                                   'image_name': image_names})

    except Exception as e:
        print(f"ERROR: Issue with crawling pages")
        images = None

    return driver, images


def download_annotations(driver, source_id, source_dir):
    """
    This function downloads the annotations from a CoralNet source.
    """

    # To hold the annotations
    annotations = None

    # The URL of the source page
    source_url = CORALNET_URL + f"/source/{source_id}/browse/images/"

    # Send a GET request to the login page to retrieve the login form
    response = requests.get(LOGIN_URL)

    # Pass along the cookies
    cookies = response.cookies

    # Parse the HTML of the response using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the CSRF token from the HTML of the login page
    csrf_token = soup.find("input", attrs={"name": "csrfmiddlewaretoken"})

    # Create a dictionary with the login form fields and their values
    # (replace "username" and "password" with your actual username and
    # password)
    data = {
        "username": driver.capabilities['credentials']['username'],
        "password": driver.capabilities['credentials']['password'],
        "csrfmiddlewaretoken": csrf_token["value"],
    }

    # Include the "Referer" header in the request
    headers = {
        "Referer": LOGIN_URL,
    }

    # Use requests.Session to create a session that will maintain your login state
    with requests.Session() as session:

        # Use session.post() to submit the login form, including the "Referer" header
        response = session.post(LOGIN_URL,
                                data=data,
                                headers=headers,
                                cookies=cookies)

        try:
            # Use session.get() to make a GET request to the source URL
            response = session.get(source_url,
                                   data=data,
                                   headers=headers,
                                   cookies=cookies)

            # Pass along the cookies
            cookies = response.cookies

            # Get the status of the source
            status = response.text.split(".")[0]

            # Check the response to see if the source exists and the user has access to it
            if "Page could not be found" in status or "don't have permission" in status:
                raise Exception(f"ERROR: {status} or you do not have permission to access it")

            # Download the annotations
            print(f"NOTE: Downloading annotations for source {source_id}")

            # Parse the HTML response using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the form in the HTML
            form = soup.find("form", {"id": "export-annotations-form"})

            # If form comes back empty, it's likely the credentials are incorrect
            if form is None:
                raise Exception(f"ERROR: Issue with downloading annotations; form is not enabled")

            # Extract the form fields (input elements)
            inputs = form.find_all("input")

            # Create a dictionary with the form fields and their values
            data = {'optional_columns': []}
            for i, input in enumerate(inputs):
                if i == 0:
                    data[input["name"]] = input["value"]
                else:
                    data['optional_columns'].append(input['value'])

            # Use session.post() to submit the form
            response = session.post(CORALNET_URL + form["action"],
                                    data=data,
                                    headers=headers,
                                    cookies=cookies)

            # Check the response status code
            if response.status_code == 200:
                # Convert the text in response to a dataframe
                annotations = pd.read_csv(io.StringIO(response.text), sep=",")
                # Save the dataframe locally
                annotations.to_csv(source_dir + "annotations.csv")

                if not os.path.exists(source_dir + "annotations.csv"):
                    raise Exception("ERROR: Issue with saving annotations")
                else:
                    print("NOTE: Annotations saved successfully")

            else:
                raise Exception("ERROR: Could not submit form, likely due to a timeout")

        except Exception as e:
            print(f"ERROR: Issue with downloading annotations")
            annotations = None

    return driver, annotations


def download_data(driver, source_id, output_dir):
    """
    This function serves as the front for downloading all the data
    (labelset, model metadata, annotations and images) for a source. This
    function was made so that multiprocessing can be used to download the
    data for multiple sources concurrently.
    """

    # The directory to store the output
    source_dir = os.path.abspath(output_dir) + f"\\{str(source_id)}\\"
    image_dir = source_dir + "images\\"

    # Creating the directories
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Update the download directory in the driver
    download_settings = {
        "behavior": "allow",
        "downloadPath": source_dir
    }

    driver.execute_cdp_cmd('Page.setDownloadBehavior', download_settings)

    try:
        # Get the metadata of the trained model, then save.
        driver, meta = download_metadata(driver, source_id, source_dir)
        # Print if there is no trained model.
        if meta is None:
            raise Exception(f"ERROR: Source {source_id} may not have a trained model")

    except Exception as e:
        print(f"ERROR: Unable to get model metadata from source {source_id}\n{e}")
        meta = None

    try:
        # Get the labelset, then save.
        driver, labelset = download_labelset(driver, source_id, source_dir)
        # Print if there is no labelset.
        if labelset is None:
            raise Exception(f"ERROR: Source {source_id} may not have a labelset")

    except Exception as e:
        print(f"ERROR: Unable to get labelset from source {source_id}\n{e}")
        labelset = None

    try:
        # Get the images for the source
        driver, images = get_images(driver, source_id)

        if images is not None:
            # Get the image page URLs
            image_pages = images['image_page'].tolist()
            # Get the image AWS URLs
            driver, images['image_url'] = get_image_urls(driver, image_pages)

            # Download the images to the specified directory
            download_images(images, source_dir)

        else:
            raise Exception(f"ERROR: Source {source_id} may not have any images")

    except Exception as e:
        print(f"ERROR: Unable to get images from source {source_id}\n{e}")
        images = None

    try:
        # Get all the annotations, then save.
        annotations = download_annotations(driver, source_id, source_dir)
        # Print if there are no annotations.
        if annotations is None:
            raise Exception(f"ERROR: Source {source_id} may not have any annotations")

    except Exception as e:
        print(f"ERROR: Unable to get annotations from source {source_id}\n{e}")
        print("NOTE: If there are annotations, you may need to increase the wait time variable")
        annotations = None

    return driver, meta, labelset, images, annotations


# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------

def main():
    """
    This is the main function of the script. It calls the functions
    download_labelset, download_annotations, and download_images to download
    the label set, annotations, and images, respectively.

    There are other functions that also allow you to identify all public
    sources, all labelsets, and sources containing specific labelsets.
    It is entirely possibly to identify sources based on labelsets, and
    download all those sources, or simply download all data from all
    source. Have fun!

    BE RESPONSIBLE WITH YOUR DOWNLOADS. DO NOT OVERWHELM THE SERVERS.
    """

    parser = argparse.ArgumentParser(description='CoralNet arguments')

    parser.add_argument('--username', type=str,
                        default=os.getenv('CORALNET_USERNAME'),
                        help='Username for CoralNet account')

    parser.add_argument('--password', type=str,
                        default=os.getenv('CORALNET_PASSWORD'),
                        help='Password for CoralNet account')

    parser.add_argument('--source_ids', type=int, nargs='+',
                        help='A list of source IDs to download.')

    parser.add_argument('--output_dir', type=str, default="../CoralNet_Data/",
                        help='A root directory where all downloads will be '
                             'saved to.')

    parser.add_argument('--headless', type=str, default='True',
                        choices=['True', 'False'],
                        help='Run browser in headless mode')

    args = parser.parse_args()

    # A list of sources to download
    source_ids = args.source_ids
    if source_ids is None:
        print("ERROR: Please provide a list of source IDs.")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Authenticate the user
    # -------------------------------------------------------------------------
    try:
        username = args.username
        password = args.password

        # Ensure the user provided a username and password.
        authenticate(username, password)
    except Exception as e:
        print(f"ERROR: Could not download data.\n{e}")
        sys.exit(1)

    # Output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # Get the browser
    # -------------------------------------------------------------------------
    options = Options()

    if args.headless.lower() == 'true':
        # Set headless mode
        options.add_argument("--headless")

    # Pass the options object while creating the driver
    driver = check_for_browsers(options=options)
    # Store the credentials in the driver
    driver.capabilities['credentials'] = {
        'username': username,
        'password': password
    }
    # Login to CoralNet
    driver, _ = login(driver)

    # -------------------------------------------------------------------------
    # Download the data
    # -------------------------------------------------------------------------

    try:
        for source_id in args.source_ids:
            print(f"\nNOTE: Downloading data for source {source_id}")
            driver, m, l, i, a = download_data(driver, source_id, output_dir)

    except Exception as e:
        raise Exception(f"ERROR: Could not download data\n{e}")

    finally:
        # Close the browser
        driver.close()

    print("Done.")


if __name__ == "__main__":
    main()


import copy
import io
import logging
import os
import functools
from itertools import repeat
from typing import Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor

from pypdf import PdfReader, PdfWriter

from unstructured_client import utils
from unstructured_client.models import shared
from unstructured_client.models.operations import PartitionResponse

logger = logging.getLogger('unstructured-client')


def extract_split_pdf_page(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) > 0:
            request = args[1]
        else:
            raise ValueError("Expected a request argument for the partition function.")
        split_pdf_page = request.split_pdf_page

        if not split_pdf_page:
            return func(*args, **kwargs)

        pages = get_pdf_pages(request.files.content)

        call_threads = int(os.getenv("UNSTRUCTURED_CLIENT_SPLIT_CALL_THREADS", 5))
        logger.info(f"Splitting PDF by page on client. Using {call_threads} threads when calling API. "
                    f"Set UNSTRUCTURED_CLIENT_SPLIT_CALL_THREADS if you want to change that.")

        results = []
        with ThreadPoolExecutor(max_workers=call_threads) as executor:
            if len(args) < 3:
                retries = None
            else:
                retries = args[2]
            self = args[0]

            for result in executor.map(call_api, pages, repeat(func), repeat(self), repeat(request), repeat(retries)):
                results.append(result)

            if all(result.status_code != 200 for result in results):
                resp = PartitionResponse(
                    raw_response=results[0].raw_response,
                    status_code=results[0].status_code,
                    elements=[],
                    content_type=results[0].content_type,
                )
                return resp

            first_success = next((result for result in results if result.status_code == 200))
            flattened_elements = [element for response in results
                                  if response.status_code == 200 for element in response.elements]

            resp = PartitionResponse(
                raw_response=first_success.raw_response,
                status_code=200,
                elements=flattened_elements,
                content_type=first_success.content_type,
            )
            return resp

    return wrapper


def call_api(page_tuple: Tuple[io.BytesIO, int], func: Callable, self, request: Optional[shared.PartitionParameters], retries: Optional[utils.RetryConfig] = None):
    """
    Given a single pdf file, send the bytes to the Unstructured api.
    Self is General, but can't use type here because of circular imports. The rest of parameters are like in partition().
    When we get the result, replace the page numbers in the metadata (since everything will come back as page 1)
    """

    from unstructured_client.models import errors  # pylint: disable=C0415

    page_content = page_tuple[0]
    page_number = page_tuple[1]

    try:
        new_request = copy.deepcopy(request)
        new_request.files.content = page_content

        result = func(self, new_request, retries)

        if result.status_code == 200:
            for element in result.elements:
                element["metadata"]["page_number"] = page_number

        return result

    except errors.SDKError as e:
        logger.error(e)
        return []


def get_pdf_pages(file_content: bytes, split_size: int = 1):
    """
    Given a path to a pdf, open the pdf and split it into n file-like objects, each with split_size pages
    Yield the files with their page offset in the form (BytesIO, int)
    """

    pdf = PdfReader(io.BytesIO(file_content))
    pdf_pages = pdf.pages
    offset = 0

    while offset < len(pdf_pages):
        new_pdf = PdfWriter()
        pdf_buffer = io.BytesIO()

        end = offset + split_size
        for page in pdf_pages[offset:end]:
            new_pdf.add_page(page)

        new_pdf.write(pdf_buffer)
        pdf_buffer.seek(0)

        # 1-index the page numbers
        yield pdf_buffer, offset+1
        offset += split_size

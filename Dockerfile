FROM public.ecr.aws/lambda/python:3.12-arm64

# Copy requirements.txt file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY ./helpers ${LAMBDA_TASK_ROOT}/helpers
COPY credentials.py ${LAMBDA_TASK_ROOT}

# Set the CMD to the handler
CMD [ "lambda_function.handler" ]
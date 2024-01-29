FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install requirements
RUN pip install -r requirements.txt

# Copy function code
COPY lamda_function.py ${LAMBDA_TASK_ROOT}
COPY ./helpers ${LAMBDA_TASK_ROOT}/helpers
COPY config.py ${LAMBDA_TASK_ROOT}

# Set the CMD to the handler
CMD [ "lamda_function.handler" ]
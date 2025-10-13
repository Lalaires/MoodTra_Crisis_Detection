FROM public.ecr.aws/lambda/python:3.13 

COPY requirements.txt  ${LAMBDA_TASK_ROOT} 
  
# Install function dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY main.py ${LAMBDA_TASK_ROOT}
COPY crisis_pipeline.py ${LAMBDA_TASK_ROOT}

# Set environment variables
ENV DB_HOST=url_to_db   
ENV DB_NAME=name_of_db
ENV DB_USER=user_of_db
ENV DB_PASSWORD=password_of_db
ENV DB_PORT=port_of_db
ENV HF_HOME=/tmp/hf 
ENV GOOGLE_API_KEY=gemini_api_key

# Set the CMD to your handler
CMD [ "main.lambda_handler" ]
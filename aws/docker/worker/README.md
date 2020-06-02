## GliderDAC queue processing worker

Right now only handles one job from the 'gliderdac-profile-plot-generation' AWS SQS. This container is deployed using AWS ECS.

Need to provide the following Environment Vars to run:
SQS_URL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION

Ask the GliderDAC system admin if you need access.
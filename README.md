# VirtualEye - Life Guard for Swimming Pools to Detect Active Drowning - Development Stage

## Project Description:

Swimming is one of the best exercises that helps people to reduce stress in this urban lifestyle. Swimming pools are found larger in number in hotels, and weekend tourist spots and barely people have them in their house backyard. Beginners, especially, often feel it difficult to breathe underwater which causes breathing trouble which in turn causes a drowning accident. Worldwide, drowning produces a higher rate of mortality without causing injury to children. Children under six of their age are found to be suffering the highest drowning mortality rates worldwide. Such kinds of deaths account for the third cause of unplanned death globally, with about 1.2  million cases yearly. To overcome this conflict, a meticulous system is to be implemented along the swimming pools to save human life. 

By studying body movement patterns and connecting cameras to artificial intelligence (AI) systems we can devise a pool safety system that reduces the risk of drowning.  Usually, such systems can be developed by installing more than 16 cameras underwater and ceiling and analyzing the video feeds to detect any anomalies. But as a POC we make use of one camera that streams the video of the water and analyses the position of swimmers to assess the probability of drowning, if it is higher than an alert will be generated to attract lifeguards' attention.

## Prerequisites

- Python 3.7 +
- CUDA 11.7 (Optional)
- IBM Cloudant DB Service
- Send Grid Email API

## Build Instructions

Install required python libraries using following command in the Terminal from the project directory :
```
pip install -r requirements.txt
```

Now create a database for user login in Cloudant DB (from Cloudant DB Dashboard)

Now create environment file (.env file) in your project directory. It should contain following fields,
- FLASK_ENV
- FLASK_DEBUG
- CLOUDANT_URL
- CLOUDANT_APIKEY
- VIRTUAL_EYE_START_SALT
- VIRTUAL_EYE_END_SALT
- User_DB
- SENDGRID_APIKEY
- SENDGRID_FROM_MAIL
- SENDGRID_REGISTER_TEMPLATE_ID
- SENDGRID_FORGOT_PASSWORD_TEMPLATE_ID

Sample of .env file is given below :
```
FLASK_ENV=development
FLASK_DEBUG=true
CLOUDANT_URL=<Your Cloudant Service URL>
CLOUDANT_APIKEY=<Your Cloudant Service API key>
VIRTUAL_EYE_START_SALT=sample1
VIRTUAL_EYE_END_SALT=sample2
USER_DB=<Your Cloudant DB User Database name>
SENDGRID_APIKEY=<Your SendGrid API key>
SENDGRID_FROM_MAIL=<Your SendGrid Authorized Sender Mail ID>
SENDGRID_REGISTER_TEMPLATE_ID=<Your SendGrid Dynamic Template ID for Registration Success Mail>
SENDGRID_FORGOT_PASSWORD_TEMPLATE_ID=<Your SendGrid Dynamic Template ID for Forgot Password Mail>
```

## Usage Instructions

Run the following command in Terminal from project directory to start the application :
```
flask run
```

Now open http://127.0.0.1:5000/ in your browser to access the application
<< AWS_Lex-Bot_setup >>
## Selected us-east-1 as a region
## Amazon Lex setup:

1. created a traditional blank bot
2. named it as HotelBookingBot
3. selected iam role for basic amazon lex permission
4. selected no for COPPA
5. selected english as a language:   
	a. created an intent with a name BookHotel.

	b. created sample utterances which has phases that should be used by the user (content present in utterances.txt).

	c. created slots that will be asked by the chatbot to the user (content present in slot_data.txt)

	d. created custom slot types for :

            1. RoomTypeValues having values : [Classic,Duluxe,Suite,Duplex,PentaHouse]
            2. BedType having values : [king bed,Twin bed,Double queen bed,Single bed]
            3. Smoking having values : [non smoking room,smoking room,non smoking,smoking]
            4. PaymentMethod having values : [Credit card,Debit Card,Pay on arrival,Pay at Hotel]
	e. created confirmation :

		1. confirmation prompt : You're booking a {RoomType} room in {City} ( {HotelName} Hotel Name is provided) for {NumAdults} adult(s) (and {NumChildren} child/children, if applicable). Your check-in date is {CheckInDate} for {NumNights} night(s). We'll confirm the booking to {ContactEmail} or contact {ContactPhone}. Should I go ahead with the booking?
		2. decline response : No problem. Let me know if you change your mind.


	f. created fulfilment :

		1. on successful fulfilment : "Processing your booking..."
		2. In case of failure : "Sorry, something went wrong. Please try again later."


	g. In advance option of fulfilment :

		1. enabled lambda function for fulfilment
		2. given prompt for fulfilment updates :
			a. tell the user that fulfilment has started : "The process has started..." 
			b. periodically update the user about fulfilment progress : "Progress happening"
		3. given prompt for success response :
			a. tell the user that fulfilment was completed successfully : "Processing your booking..."
		4. given prompt for failure response :
			a. Inform the user that fulfilment was not completed : "Sorry, something went wrong. Please try again later."
		5. given prompt for Timeout response :
			a. Inform the user that fulfilment reached its timeout before it was completed : "Still working on it..."


	h. disabled code hooks

	i. saved and the build the intent

	j. after chat bot built, tested the bot by adding the lambda function through setting icon.




## Lambda setup which will be trigger dynamodb and store the output of customer in the table : 

a. created a lambda function with the name HotelBookingHandler with python version 3.12
b. created code for lambda
c. created two policy for lambda :
	1. lex-lambda-invokeFunction, having json code :

			{
			  "StringEquals": {
			    "AWS:SourceAccount": "ACCOUNT_ID"
			  },
			  "ArnLike": {
			    "AWS:SourceArn": "arn:aws:lex:REGION_NAME:ACCOUNT_ID:bot-alias/BOT_ID/BOT_ALIASE_ID"
			  }
			}

and, Statement ID : lex-lambda-invokeFunction
Principal : lexv2.amazonaws.com
Effect : Allow
Action : lambda:invokeFunction


2. custom_lambda_invoke, having json code :

			{
			  "ArnLike": {
			    "AWS:SourceArn": "arn:aws:lambda:us-east-1:200997298224:function:HotelBookingLambda"
			  }
			}

and, Statement ID : custom_lambda_invoke
Principal : lexv2.amazonaws.com
Effect : Allow
Action : lambda:invokeFunction




## DynamoDB setup : 

a. created table named as HotelBooking
b. named partition key as bookingId having string format
c. created it.
d. whenever client interact with the chatbot lambda get triggered and send the client information in the created table




## Cognito setup for creation of webapp through which user can interact with aws services:

a. created one identity pool named as HotelBookingBotIdentityPool
b. given guest access
c. created and named Cognito_YourPoolNameAuth_Role as IAM role :
	1. It has one precreated cognito role and extra i  have attached a policy named as AmazonLexFullAccess
	2. also created another inline policy named as cognito_lex_setup, having json code :

			{
				"Version": "2012-10-17",
				"Statement": [
					{
						"Effect": "Allow",
						"Action": [
							"lex:PostText"
						],
						"Resource": "arn:aws:lex:REGION_NAME:ACCOUNT_ID:bot:HotelBookingBot:*"
					}
				]
			}

## Webapp setup for user to interact using EC2 :

	a. launched an ec2 instance
	b. connected to root user through : sudo su - root
	c. install apache server : yum install httpd
	d. started apache server : systemctl enable httpd --now
	e. changed to path created by apache server : cd var/www/html
	f. created a file named hotel_booking.html and created a code having aws credentials that will contact to aws.

 

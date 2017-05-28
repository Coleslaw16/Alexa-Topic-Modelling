from TwitterSearch import *
from gensim import corpora, models
import gensim
import pandas as pd
from nltk.corpus import stopwords
from collections import defaultdict
import re
import time

SKILL_NAME = "Twitter Sustainability Topic Model"
def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID
    to prevent someone else from configuring a skill that sends requests
    to this function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])



def on_session_started(session_started_request, session):
    print("on_session_started requestId=" +
          session_started_request['requestId'] + ", sessionId=" +
          session['sessionId'])



def on_launch(launch_request, session):
    """Called when the user launches the skill without specifying what they want."""
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """Called when the user specifies an intent for this skill."""
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # handle yes/no intent after the user has been prompted
    if session.get('attributes', {}).get('user_prompted_to_continue'):
        del session['attributes']['user_prompted_to_continue']
        if intent_name == 'AMAZON.NoIntent':
            return handle_finish_session_request(intent, session)
        elif intent_name == "AMAZON.YesIntent":
            return handle_repeat_request(intent, session)

    # Dispatch to your skill's intent handlers
    if intent_name == "TopicIntent":
        return handle_answer_request(intent, session)
    elif intent_name == "NextIntent":
        return handle_next(intent, session)
    elif intent_name == "AMAZON.YesIntent":
        return handle_yes(intent, session)
    elif intent_name == "AMAZON.NoIntent":
        return handle_next(intent, session)
    elif intent_name == "AMAZON.StartOverIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.RepeatIntent":
        return handle_repeat_request(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_get_help_request(intent, session)
    elif intent_name == "AMAZON.StopIntent":
        return handle_finish_session_request(intent, session)
    elif intent_name == "AMAZON.CancelIntent":
        return handle_finish_session_request(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """
    Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior -------------


def get_welcome_response():
    """If we wanted to initialize the session to have some attributes we could add those here."""
    intro = ("Hello, please ask about a subject in sustainability to here the topics trending about it on twitter.")
    reprompt_texts = ( "Please ask about a subject in sustainability to here the topics trending about it on twitter.")
    should_end_session = False

    attributes = {"speech_output": intro,
                  "reprompt_text": reprompt_texts
                 }

    return build_response(attributes, build_speechlet_response(
        SKILL_NAME, intro, reprompt_texts, should_end_session))


def populate_tweet_topics(intent, session, answer):
    twitterText = []

    try: 
        tso = TwitterSearchOrder()
        tso.add_keyword(answer)
        tso.set_geocode(38.328732, -85.764771, 35)
    
        ts = TwitterSearch(
            consumer_key = 'consumer_key',
            consumer_secret = 'consumer_secret',
            access_token = 'access_token',
            access_token_secret = 'access_token_secret'
        )

        for tweets in ts.search_tweets_iterable(tso):
            twitterText.append(tweets['text'])
    except TwitterSearchException as e:
        print(e)



    documents = twitterText
    documents = [' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z# \t])|(\w+:\/\/\S+)", " ", doc.strip()).split()) for doc in documents]
    documents = [' '.join([w for w in doc.split() if not w.isdigit() and len(w) > 1]) for doc in documents]
    print('Done Reading Data')
 
    # Remove stopwords
    cached_stopwords = set(stopwords.words('english'))
    cached_stopwords.update([word for line in open('stopwords.txt', 'r') for word in line.split()])  # read from stopwords file
    cached_stopwords.update(['rt', 'https', 'http', 'htt', 'gt', 'p', 'amp', 'a', 'about', 'above', 'above', 'across', 'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone', 'along', 'already', 'also', 'although', 'always', 'am', 'among', 'amongst', 'amoungst', 'amount',  'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around', 'as',  'at', 'back', 'be', 'became', 'because', 'become', 'becomes', 'becoming', 'been', 'before', 'beforehand', 'behind', 'being', 'below', 'beside', 'besides', 'between', 'beyond', 'bill', 'both', 'bottom', 'but', 'by', 'call', 'can', 'cannot', 'cant', 'co', 'con', 'could', 'couldnt', 'cry', 'de', 'describe', 'detail', 'do', 'done', 'dont', 'down', 'due', 'during', 'each', 'eg', 'eight', 'either', 'eleven', 'else', 'elsewhere', 'empty', 'enough', 'etc', 'even', 'ever', 'every', 'everyone', 'everything', 'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 'formerly', 'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get', 'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it', 'its', 'itself', 'keep', 'last', 'latter', 'latterly', 'least', 'less', 'ltd', 'made', 'many', 'may', 'me', 'meanwhile', 'might', 'mill', 'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much', 'must', 'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not', 'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once', 'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per', 'perhaps', 'please', 'put', 'rather', 're', 'same', 'see', 'seem', 'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 'should', 'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still', 'such', 'system', 'take', 'ten', 'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'thence', 'there', 'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'thickv', 'thin', 'third', 'this', 'those', 'though', 'three', 'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under', 'until', 'up', 'upon', 'us', 'very', 'via', 'was', 'we', 'well', 'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon', 'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves', 'the'])
 
    texts = [[word for word in document.lower().split() if word not in cached_stopwords] for document in documents]
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    texts = [[token for token in text if frequency[token] > 1] for text in texts]  # keep only the words that occured atleast twice in the dataset
 

    return texts, twitterText



def handle_answer_request(intent, session):
    attributes = {}
    should_end_session = False
    answer = intent['slots'].get('Answer', {}).get('value')
    user_gave_up = intent['name']

    if not answer and user_gave_up == "DontKnowIntent":
        # If the user provided answer isn't a number > 0 and < ANSWER_COUNT,
        # return an error message to the user. Remember to guide the user
        # into providing correct values.
        reprompt = session['attributes']['speech_output']
        reprompt_text = session['attributes']['reprompt_text']
        speech_output = "Your answer must be a known sustainability subject. " + reprompt
        return build_response(
            session['attributes'],
            build_speechlet_response(
                SKILL_NAME, speech_output, reprompt_text, should_end_session
            ))
    else:
        texts, twitter_texts = populate_tweet_topics(intent, session, answer)
        dictionary = corpora.Dictionary(texts)
    
        # convert tokenized documents into a document-term matrix
        corpus = [dictionary.doc2bow(text) for text in texts]

        # generate LDA model
        ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=5, id2word = dictionary, passes=20)
        print(ldamodel.print_topics(num_topics=5, num_words=20))

        bmlda = ldamodel[corpus]
        largest = {}
        topics = []
        tweet = []
        index = 0

        for index, t in enumerate(texts):
            z = ldamodel[dictionary.doc2bow(texts[index])]
            for i in z:
                if i[0] in largest:
                    if i[1] > largest[i[0]][0]:
                        largest[i[0]] = (i[1], index)
                else:
                    largest[i[0]] = (i[1], index)
        
        for i in range(10):
            tweet.append(twitter_texts[largest[i][1]])
            
        
        for i in range(10):
            well_crap = ldamodel.get_topic_terms(i, 5) 
            topic_holders = ''
            for t in range(5):
                topic_holders = topic_holders +  " " + dictionary[well_crap[t][0]]
            topics.append(topic_holders)
        
        speech_output = "A topic was " + topics[index] + " would you like to hear the top tweet from this topic? You may also say next to continue to next topic" 
        
        attributes = {"speech_output": speech_output,
                          "reprompt_text": speech_output,
                          "current_topic_index": index,
                          "topics": topics,
                          "tweets": tweet,
                    }

        return build_response(attributes,
                                  build_speechlet_response(SKILL_NAME, speech_output, reprompt_text,
                                                           should_end_session))


def handle_repeat_request(intent, session):
    """
    Repeat the previous speech_output and reprompt_text from the session['attributes'].
    If available, else start a new game session.
    """
    if 'attributes' not in session or 'speech_output' not in session['attributes']:
        return get_welcome_response()
    else:
        attributes = session['attributes']
        speech_output = attributes['speech_output']
        reprompt_text = attributes['reprompt_text']
        should_end_session = False
        return build_response(
            attributes,
            build_speechlet_response_without_card(speech_output, reprompt_text, should_end_session)
        )


def handle_get_help_request(intent, session):
    attributes = {}
    speech_output = ("Please say a sustainability topic, or you can say exit")
    reprompt_text = "What can I help you with?"
    should_end_session = False
    return build_response(
        attributes,
        build_speechlet_response(SKILL_NAME, speech_output, reprompt_text, should_end_session)
    )


def handle_finish_session_request(intent, session):
    attributes = session['attributes']
    reprompt_text = None
    speech_output = "Thanks for playing {}!".format(SKILL_NAME)
    should_end_session = True
    return build_response(
        attributes,
        build_speechlet_response_without_card(speech_output, reprompt_text, should_end_session)
    )



def handle_next(intent, session):
    should_end_session = False
    if 'current_topic_index' not in session['attributes'].keys():
        speech_output = "Please ask about a subject first"
        reprompt_text = "Say a subject"
        attributes = {"speech_output": speech_output,
                      "reprompt_text": reprompt_texts
                     }

        return build_response(attributes, build_speechlet_response(
            SKILL_NAME, intro, reprompt_texts, should_end_session))
    else:
        index = session['attributes']['current_topic_index']
        tweets = session['attributes']['tweets']
        topics = ['attributes']['topics']
        index += 1
        if index == 10:
            speech_output = "A topic was " + topics[index] + " would you like to hear the top tweet from this topic?" 
        elif index == 11:
            return handle_finish_session_request(intent, session)
        else:
            speech_output = "A topic was " + topics[index] + " would you like to hear the top tweet from this topic? You may also say next to continue to next topic" 
        attributes = {"speech_output": speech_output,
                          "reprompt_text": speech_output,
                          "current_topic_index": index,
                          "topics": topics,
                          "tweets": tweet,
                    }

        return build_response(attributes,
                                  build_speechlet_response(SKILL_NAME, speech_output, reprompt_text,
                                                           should_end_session))
            

def handle_yes(intent, session):
    should_end_session = False
    if 'current_topic_index' not in session['attributes'].keys():
        speech_output = "Please ask about a subject first"
        reprompt_text = "Say a subject"
        attributes = {"speech_output": speech_output,
                      "reprompt_text": reprompt_texts
                     }

        return build_response(attributes, build_speechlet_response(
            SKILL_NAME, intro, reprompt_texts, should_end_session))
    else:
        index = session['attributes']['current_topic_index']
        tweets = session['attributes']['tweets']
        topics = ['attributes']['topics']
        index += 1
        if index == 10:
            speech_output = "The tweet was " + tweets[index] + " . Goodbye!"
            should_end_session = True 
        else:
            speech_output = "The tweet was " + tweets[index] + ". You may also say next to continue to next topic" 
        attributes = {"speech_output": speech_output,
                          "reprompt_text": speech_output,
                          "current_topic_index": index,
                          "topics": topics,
                          "tweets": tweet,
                    }

        return build_response(attributes,
                                  build_speechlet_response(SKILL_NAME, speech_output, reprompt_text,
                                                           should_end_session))



# --------------- Helpers that build all of the responses -----------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_speechlet_response_without_card(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': attributes,
        'response': speechlet_response
    }
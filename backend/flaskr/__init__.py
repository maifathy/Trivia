import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# handle pagination
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  
  return current_questions

# handle current_category
def paginate_questions_current_categories(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  category_ids = [question.category for question in selection[start:end]]
  current_category_query = Category.query.filter(Category.id.in_(category_ids)).all()
  current_category = {category.id: category.type for category in current_category_query}
  return current_category

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  # Set up CORS. Allow '*' for origins.
  CORS(app, resources={r"/api/*": {"origins": "*"}})

  # Use the after_request decorator to set Access-Control-Allow
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  # Create an endpoint to handle GET requests for all available categories.
  @app.route('/categories')
  def retrieve_categories():
    selection = Category.query.order_by(Category.id).all()
    current_categories = {category.id: category.type for category in selection}
    
    if len(current_categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': current_categories
    })


 
  # Create an endpoint to handle GET requests for questions, 
  # including pagination (every 10 questions)
  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
      abort(404)
    
    current_category = paginate_questions_current_categories(request, selection)

    categories = Category.query.order_by(Category.id).all()
    formatted_categories = {category.id: category.type for category in categories}
    
    if len(formatted_categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(selection),
      'current_category': current_category,
      'categories': formatted_categories
    })

  # Create an endpoint to DELETE question using a question ID. 
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      return jsonify({
        'success': True,
        'deleted': question_id
      })

    except:
      abort(422)

  # Create an endpoint to POST a new question, 
  # support search by sending 'searchTerm'
  @app.route('/questions', methods=['POST'])
  def create_search_question():
    body = request.get_json()

    question = body.get('question', None)
    answer = body.get('answer', None)
    category = body.get('category', None)
    difficulty = body.get('difficulty', None)
    # update to allow search 
    search = body.get('searchTerm', None)

    try:
      if search is not None:
        selection = Question.query.order_by(Question.id)\
          .filter(Question.question.ilike('%' + search + '%'))\
          .all()
        current_questions = paginate_questions(request, selection)
        current_category = paginate_questions_current_categories(request, selection)

        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(selection),
          'current_category': current_category
        })
      else:
        new_question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
        new_question.insert()

        return jsonify({
          'success': True,
          'created': new_question.id
        })

    except:
      abort(422)

  # Create a GET endpoint to get questions based on category. 
  @app.route('/categories/<int:id>/questions')
  def retrieve_questions_by_categories(id):
    selection = Question.query.order_by(Question.id).filter(Question.category==id).all()
    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(selection),
      'current_category': id
    })


  # Create a POST endpoint to get questions to play the quiz,
  # by category and previous questions.
  # Questions are random and are not repeated
  @app.route('/quizzes', methods=['POST'])
  def retrieve_quiz_question():
    try:
      body = request.get_json()
      
      if body.get('quiz_category')['id'] == 0:
        new_question = Question.query.order_by(Question.id)\
            .filter(~Question.id.in_(body.get('previous_questions', None)))\
            .order_by(func.random()).limit(1).all()
      else:
        new_question = Question.query.order_by(Question.id)\
            .filter(~Question.id.in_(body.get('previous_questions', None)))\
            .filter(Question.category == body.get('quiz_category')['id'])\
            .order_by(func.random()).limit(1).all()
      
      if len(new_question) == 0: 
        question =  None 
      else:
        question = new_question[0].format()

      return jsonify({
        'success': True,
        'question': question
      })
    except: 
      abort(422)

  #Create error handlers for all expected errors 
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success' : False,
      'message' : 'Resource not found.',
      'error' : 404
    }), 404

  @app.errorhandler(400)
  def cannot_perform(error):
    return jsonify({
      'success' : False,
      'message' : 'cannot perform the action, a client error is existing.',
      'error' : 400
    }), 400

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success' : False,
      'message' : 'Operation is unprocessable.',
      'error' : 422
    }), 422

  @app.errorhandler(405)
  def not_found(error):
    return jsonify({
      'success' : False,
      'message' : 'Method not allowed.',
      'error' : 405
    }), 405
  return app

    
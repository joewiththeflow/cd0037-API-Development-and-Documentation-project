import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category
from settings import DB_TEST_NAME, DB_USER, DB_PASSWORD


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_path = "postgres://{}/{}".format('localhost:5432', DB_TEST_NAME)
        setup_db(self.app, self.database_path)

        self.new_question = {
            "question": "What is the capital of England?", 
            "answer": "London", 
            "category": 3,
            "difficulty": 2
            }
        
        self.new_question_wrong_category = {
            "question": "What is the capital of England?", 
            "answer": "London", 
            "category": 1000,
            "difficulty": 2
            }
        
        self.next_question_category_3 = {
            'previous_questions': [], 
            'quiz_category': {'id': 3, 'type': 'Geography'},
            }
        
        self.next_question_category_0 = {
            'previous_questions': [], 
            'quiz_category': {'id': 0, 'type': 'click'},
            }
        
        self.next_question_category_unknown = {
            'previous_questions': [], 
            'quiz_category': {'id': 1000, 'type': 'blah'},
            }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    # GET CATEGORIES

    def test_retrieve_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["categories"]))

    def test_405_create_category_not_allowed(self):
        res = self.client().post("/categories", json={"id": 7, "type": "Archaeology"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "method not allowed")



    # GET QUESTIONS

    def test_retrieve_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(data["categories"])
        self.assertTrue(len(data["questions"]))


    def test_retrieve_questions_with_valid_page(self):
        res = self.client().get("/questions?page=2")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["total_questions"])
        self.assertTrue(data["categories"])
        self.assertTrue(len(data["questions"]))


    def test_404_retrieve_questions_beyond_valid_page(self):
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")


    # DELETE QUESTION

    # Can only run this once successfully, then need to dropdb and recreate
    # def test_delete_question(self):
    #     res = self.client().delete('/questions/2')
    #     data = json.loads(res.data)

    #     question = Question.query.filter(Question.id == 2).one_or_none()

    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(data['success'], True)
    #     self.assertEqual(data['deleted'], 2)
    #     self.assertEqual(question, None)


    def test_404_if_question_does_not_exist(self):
        res = self.client().delete("/questions/1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")


    # CREATE QUESTION

    def test_create_new_question(self):
        res = self.client().post("/questions", json=self.new_question)
        data = json.loads(res.data)
        
        # Get last question in db
        question = Question.query.order_by(Question.id.desc()).first()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["created"], question.id)
        self.assertTrue(data["questions"])
        self.assertTrue(data["total_questions"])


    def test_422_if_question_creation_fails_wrong_category(self):
        res = self.client().post("/questions", json=self.new_question_wrong_category)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code,422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")
        

    # SEARCH QUESTIONS
    def test_get_question_search_with_results(self):
        res = self.client().post("/questions", json={"searchTerm": "ici"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 2)
        self.assertTrue(data['total_questions'])

    
    def test_get_question_search_without_results(self):
        res = self.client().post("/questions", json={"searchTerm": "mississippi"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(len(data["questions"]), 0)
        self.assertEqual(data['total_questions'], 0)


    def test_405_get_question_search_with_wrong_method(self):
        res = self.client().patch("/questions", json={"searchTerm": "mississippi"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")
       


    # GET QUESTIONS BY CATEGORY ID
    def test_retrieve_questions_by_category(self):
        res = self.client().get("/categories/1/questions")
        data = json.loads(res.data)

        # Number of questions for category
        count = Question.query.filter(
            Question.category == 1).count()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertEqual(data["total_questions"], count)


    def test_422_retrieve_questions_by_unknown_category(self):
        res = self.client().get("/categories/1000/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertTrue(data["message"], "resource not found")



    # NEXT QUESTION IN CATEGORY DURING QUIZ
    def test_get_question_for_category(self):
        res = self.client().post("/quizzes", json=self.next_question_category_3)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])
    

    def test_get_question_for_category_all(self):
        res = self.client().post("/quizzes", json=self.next_question_category_0)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])


    def test_404_get_question_for_category_unknown(self):
        res = self.client().post("/quizzes", json=self.next_question_category_unknown)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
from app.extensions import db
from datetime import datetime
import json


class RecommendationHistory(db.Model):
    __tablename__ = 'recommendation_history'

    id          = db.Column(db.Integer,  primary_key=True)
    farmer_id   = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False)

    # Input conditions
    temperature = db.Column(db.Float,    nullable=False)
    rainfall    = db.Column(db.Float,    nullable=False)
    altitude    = db.Column(db.Float,    nullable=False)
    soil_type   = db.Column(db.String(50), nullable=False)
    soil_ph     = db.Column(db.Float,    nullable=False)

    # Results stored as JSON string
    results_json = db.Column(db.Text,   nullable=False)

    # Top crop for quick access
    top_crop        = db.Column(db.String(60),  nullable=False)
    top_confidence  = db.Column(db.Float,       nullable=False)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    farmer = db.relationship('User', backref='recommendations')

    def set_results(self, results):
        self.results_json = json.dumps(results)

    def get_results(self):
        return json.loads(self.results_json)

    def __repr__(self):
        return f'<Recommendation {self.top_crop} for farmer {self.farmer_id}>'
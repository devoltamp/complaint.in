const mongoose = require('mongoose');

const complaintSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  category: { type: String, required: true },
  urgency: { type: String, enum: ['low', 'medium', 'high', 'critical'], default: 'medium' },
  status: { type: String, enum: ['open', 'review', 'resolved'], default: 'open' },
  location: {
    city: { type: String, required: true },
    state: { type: String, required: true }
  },
  tags: [{ type: String }],
  proofs: [{ type: String }], // Store URLs or placeholder icons
  authResponse: { type: String, default: '' },
  author: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  upvotes: { type: Number, default: 0 },
  downvotes: { type: Number, default: 0 },
  commentCount: { type: Number, default: 0 },
  isPinned: { type: Boolean, default: false },
  isViral: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now },
  resolvedAt: { type: Date }
});

// Virtual for net votes
complaintSchema.virtual('netVotes').get(function() {
  return this.upvotes - this.downvotes;
});

complaintSchema.set('toJSON', { virtuals: true });
complaintSchema.set('toObject', { virtuals: true });

module.exports = mongoose.model('Complaint', complaintSchema);
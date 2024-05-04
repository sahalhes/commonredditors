from flask import Flask, render_template, request, send_file
import pandas as pd
from io import BytesIO
import praw

app = Flask(__name__)

reddit = praw.Reddit("my_bot") # Use the credentials stored in praw.ini


def get_common_users(subreddits):
    common_users = None
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        submission_authors = {submission.author.name for submission in subreddit.hot() if submission.author}
        comment_authors = {comment.author.name for comment in subreddit.comments() if comment.author}
        users = submission_authors.union(comment_authors)
        print(f"Subreddit: {subreddit_name}")
        print(f"Submission authors: {submission_authors}")
        print(f"Comment authors: {comment_authors}")
        if common_users is None:
            common_users = users
        else:
            common_users = common_users.intersection(users)
    print(f"Common users: {common_users}")
    return list(common_users)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    subreddit1 = request.form['subreddit1']
    subreddit2 = request.form['subreddit2']
    subreddits = [subreddit1, subreddit2]
    common_users = get_common_users(subreddits)
    
    # Create a dictionary to store submission authors for each subreddit
    submission_authors_dict = {} 
    max_length = 0  # Track the maximum length of author sets
    
    # Retrieve submission authors for each subreddit and find the maximum length
    for subreddit in subreddits:
        subreddit_authors = set()
        subreddit_instance = reddit.subreddit(subreddit)
        for submission in subreddit_instance.hot():
            if submission.author:
                subreddit_authors.add(submission.author.name)
        submission_authors_dict[subreddit] = subreddit_authors
        max_length = max(max_length, len(subreddit_authors))
    
    # Pad author sets with None to ensure all sets have the same length
    for subreddit, authors in submission_authors_dict.items():
        submission_authors_dict[subreddit] = list(authors) + [None] * (max_length - len(authors))
    
    # Add common users to the dictionary
    submission_authors_dict['Common Users'] = list(common_users) + [None] * (max_length - len(common_users))
    
    # Create DataFrame with a column for each subreddit's submission authors and common users
    df = pd.DataFrame(submission_authors_dict)
    
    # Create Excel file in memory
    excel_file = BytesIO()
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Common Users')
    writer.close()
    excel_file.seek(0)
    
    # Serve Excel file as downloadable attachment
    return send_file(
        excel_file,
        as_attachment=True,
        attachment_filename='common_users.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




if __name__ == '__main__':
    app.run(debug=True)

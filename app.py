from flask import Flask, render_template, request
import pandas as pd
import numpy as np

import json
app = Flask(__name__)

default_max_chip=[50,50,50,50,100]




@app.route("/", methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':


        form_data = request.form
        email = form_data.get('white_value')

        print( form_data.get('buyin'))

        ChipValues=[form_data.get('black_value'),form_data.get('green_value'),form_data.get('blue_value'),form_data.get('red_value'),form_data.get('white_value')]
        ChipValues=[float(x) for x in ChipValues]

        min_chip_counts= [form_data.get('black_min'),form_data.get('green_min'),form_data.get('blue_min'),form_data.get('red_min'),form_data.get('white_min')]
        min_chip_counts=[int(x) for x in min_chip_counts]

        max_chip_counts=[form_data.get('black_max'),form_data.get('green_max'),form_data.get('blue_max'),form_data.get('red_max'),form_data.get('white_max')]
        max_chip_counts=[int(x) for x in max_chip_counts]

        buyIn=int(form_data.get('buyin'))
        num_players=int(form_data.get('num_players'))


        try:
            for x in range(5):
                if max_chip_counts[x] ==0:
                    max_chip_counts[x]=default_max_chip[x]/num_players
        except:
            print()




        PositiveIntSolToSpan_sorted = sort_2dlist(PositiveIntSolToSpan(ChipValues,buyIn,max_chip_counts,min_chip_counts))

        df = pd.DataFrame(PositiveIntSolToSpan_sorted, columns=['Black', 'Green', 'Blue', 'Red', 'White'])
        df= df.iloc[::-1, ::-1]
        df = df.sort_values(by='White',ascending=False)
        html_table = color_code_df(df)
        return render_template('simple.html',  tables=[html_table], titles=df.columns.values)

    user_agent = request.headers.get('User-Agent')

    # Detect if the user is on mobile or desktop
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        return render_template('mobile.html')
    else:
        return render_template('index.html')
    return render_template('mobile.html')



def color_code_df(df):
    # Start building the HTML table
    html = '<table border="1" style="border-collapse: collapse;">'

    # Add table headers
    html += '<tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr>'

    # Add table rows
    for j in range(len(df)):
        html += '<tr>'
        for i in range(len(df.columns)):
            # Apply class based on the column index
            html += f'<td class="col-{i + 1}">{df.iloc[j, i]}</td>'
        html += '</tr>'

    html += '</table>'
    return html



def PositiveIntSolToSpan(ChipValues,buyIn,max_chip_counts,min_chip_counts):
    coefficients, total, max_chip_counts,min_chip_counts = ChipValues,buyIn,max_chip_counts,min_chip_counts
    var_ranges = [np.arange(0, int(total/coefficients[0])+1)]*len(coefficients)

    num_vars = len(coefficients)

    grids = np.meshgrid(*var_ranges[:-1])

    solution= []


    sum_terms = np.zeros_like(grids[0], dtype=float)
    for i in range(num_vars - 1):
        sum_terms += coefficients[i] * grids[i]

    last_var_range = var_ranges[-1]
    last_coefficient = coefficients[-1]
    last_var_grid = (total - sum_terms) / last_coefficient

    solution=[]

    grid_shape = grids[0].shape
    for index in np.ndindex(grid_shape):
        values = [int(grids[i][index]) for i in range(num_vars - 1)]
        last_var_value = last_var_grid[index]

        if last_var_value.is_integer() and last_var_value>=0:
            values = values + [int(last_var_value)]
            if checkChipCounts(values,max_chip_counts,min_chip_counts):
                solution.append(values)

    return solution


def checkChipCounts(counts,max_chip_counts,min_chip_counts):
  for x in range(len(counts)):
    if counts[x]>max_chip_counts[x] or counts[x]<min_chip_counts[x]:
      return False
  return True


def sort_2dlist(list_of_lists):
  return sorted(list_of_lists, key=lambda x: x)


if __name__ == "__main__":
    app.run(debug=True)

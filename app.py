import os
import io
import base64
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_data(filepath, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        return pd.read_csv(filepath)
    else:
        return pd.read_excel(filepath)


def calculate_bw_adjust(df, x_col=None, y_col=None):
    if x_col and y_col and x_col in df.columns and y_col in df.columns:
        group_sizes = df.groupby(x_col)[y_col].count()
        min_n = group_sizes.min() if len(group_sizes) > 0 else len(df)
    elif y_col and y_col in df.columns:
        min_n = df[y_col].count()
    elif x_col and x_col in df.columns:
        min_n = df[x_col].count()
    else:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            min_n = min(df[col].count() for col in numeric_cols)
        else:
            min_n = len(df)

    min_n = int(min_n)

    if min_n >= 100:
        return 1.0
    elif min_n >= 50:
        return 1.1
    elif min_n >= 30:
        return 1.2
    elif min_n >= 20:
        return 1.5
    elif min_n >= 10:
        return 2.0
    elif min_n >= 5:
        return 2.5
    else:
        return 3.0


def generate_violin_plot(df, x_col=None, y_col=None, title='小提琴图', figsize=(10, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    sns.set_style("whitegrid")

    bw_adjust = calculate_bw_adjust(df, x_col, y_col)

    if x_col and y_col:
        sns.violinplot(data=df, x=x_col, y=y_col, ax=ax, inner='box', bw_adjust=bw_adjust)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
    elif y_col:
        sns.violinplot(data=df, y=y_col, ax=ax, inner='box', bw_adjust=bw_adjust)
        ax.set_ylabel(y_col)
    elif x_col:
        sns.violinplot(data=df, x=x_col, ax=ax, inner='box', bw_adjust=bw_adjust)
        ax.set_xlabel(x_col)
    else:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) > 0:
            sns.violinplot(data=df[numeric_cols], ax=ax, inner='box', bw_adjust=bw_adjust)
        else:
            raise ValueError('数据中没有数值列，请选择包含数值的数据列。')

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_base64


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            df = read_data(filepath, filename)
            columns = df.columns.tolist()
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            preview = df.head(10).to_dict(orient='records')

            return jsonify({
                'success': True,
                'filename': filename,
                'columns': columns,
                'numeric_columns': numeric_columns,
                'preview': preview,
                'total_rows': len(df)
            })
        except Exception as e:
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 400

    return jsonify({'error': '不支持的文件格式，请上传 CSV 或 Excel 文件'}), 400


@app.route('/api/violin', methods=['POST'])
def violin_plot():
    data = request.get_json()
    filename = data.get('filename')
    x_col = data.get('x_col')
    y_col = data.get('y_col')
    title = data.get('title', '小提琴图')

    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在，请先上传文件'}), 400

    try:
        df = read_data(filepath, filename)
        bw_adjust = calculate_bw_adjust(df, x_col, y_col)
        img_base64 = generate_violin_plot(df, x_col=x_col, y_col=y_col, title=title)

        stats = {}
        if y_col and y_col in df.columns:
            if x_col and x_col in df.columns:
                for group in df[x_col].unique():
                    group_data = df[df[x_col] == group][y_col]
                    stats[str(group)] = {
                        'count': int(group_data.count()),
                        'mean': float(group_data.mean()),
                        'std': float(group_data.std()),
                        'min': float(group_data.min()),
                        'median': float(group_data.median()),
                        'max': float(group_data.max())
                    }
            else:
                col_data = df[y_col]
                stats['overall'] = {
                    'count': int(col_data.count()),
                    'mean': float(col_data.mean()),
                    'std': float(col_data.std()),
                    'min': float(col_data.min()),
                    'median': float(col_data.median()),
                    'max': float(col_data.max())
                }

        return jsonify({
            'success': True,
            'image': img_base64,
            'statistics': stats,
            'bw_adjust': bw_adjust
        })
    except Exception as e:
        return jsonify({'error': f'生成图表失败: {str(e)}'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

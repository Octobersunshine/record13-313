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


def calculate_bw_adjust(df, x_col=None, y_col=None, hue_col=None, y_cols=None):
    all_counts = []

    if y_cols and len(y_cols) > 0:
        for yc in y_cols:
            if yc in df.columns:
                if x_col and x_col in df.columns:
                    if hue_col and hue_col in df.columns:
                        group_sizes = df.groupby([x_col, hue_col])[yc].count()
                        if len(group_sizes) > 0:
                            all_counts.append(group_sizes.min())
                    else:
                        group_sizes = df.groupby(x_col)[yc].count()
                        if len(group_sizes) > 0:
                            all_counts.append(group_sizes.min())
                else:
                    all_counts.append(df[yc].count())
    elif y_col and y_col in df.columns:
        if x_col and x_col in df.columns:
            if hue_col and hue_col in df.columns:
                group_sizes = df.groupby([x_col, hue_col])[y_col].count()
                min_n = group_sizes.min() if len(group_sizes) > 0 else len(df)
            else:
                group_sizes = df.groupby(x_col)[y_col].count()
                min_n = group_sizes.min() if len(group_sizes) > 0 else len(df)
        else:
            min_n = df[y_col].count()
        all_counts.append(min_n)
    elif x_col and x_col in df.columns:
        all_counts.append(len(df))
    else:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            all_counts.append(min(df[col].count() for col in numeric_cols))
        else:
            all_counts.append(len(df))

    min_n = int(min(all_counts)) if all_counts else len(df)

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


def generate_violin_plot(df, x_col=None, y_col=None, hue_col=None, y_cols=None,
                        title='小提琴图', inner='box', orient='v', palette='Set2',
                        figsize=None):
    bw_adjust = calculate_bw_adjust(df, x_col, y_col, hue_col, y_cols)

    if y_cols and len(y_cols) > 0:
        plot_data = df[y_cols].copy()
        if x_col and x_col in df.columns:
            plot_data[x_col] = df[x_col]
        if hue_col and hue_col in df.columns:
            plot_data[hue_col] = df[hue_col]

        n_groups = len(y_cols)
        if x_col and x_col in df.columns:
            n_groups *= df[x_col].nunique()
        if hue_col and hue_col in df.columns:
            n_groups *= df[hue_col].nunique()
    else:
        plot_data = df
        n_groups = 1
        if x_col and x_col in df.columns:
            n_groups = df[x_col].nunique()
        if hue_col and hue_col in df.columns:
            n_groups *= df[hue_col].nunique()

    if figsize is None:
        base_width = 4 if orient == 'v' else 6
        base_height = 6 if orient == 'v' else 4
        width = max(8, base_width + n_groups * 0.8)
        height = max(6, base_height)
        figsize = (width, height)

    fig, ax = plt.subplots(figsize=figsize)
    sns.set_style("whitegrid")

    plot_params = {
        'data': plot_data,
        'ax': ax,
        'inner': inner,
        'bw_adjust': bw_adjust,
        'palette': palette,
        'orient': orient
    }

    if y_cols and len(y_cols) > 0:
        if x_col and x_col in df.columns:
            if hue_col and hue_col in df.columns:
                melted = plot_data.melt(id_vars=[x_col, hue_col], value_vars=y_cols,
                                         var_name='指标', value_name='数值')
                sns.violinplot(data=melted, x=x_col, y='数值', hue='指标',
                               ax=ax, inner=inner, bw_adjust=bw_adjust,
                               palette=palette, orient=orient)
                ax.set_xlabel(x_col)
                ax.set_ylabel('数值')
                ax.legend(title='指标', bbox_to_anchor=(1.02, 1), loc='upper left')
            else:
                melted = plot_data.melt(id_vars=[x_col], value_vars=y_cols,
                                         var_name='指标', value_name='数值')
                sns.violinplot(data=melted, x=x_col, y='数值', hue='指标',
                               ax=ax, inner=inner, bw_adjust=bw_adjust,
                               palette=palette, orient=orient)
                ax.set_xlabel(x_col)
                ax.set_ylabel('数值')
                ax.legend(title='指标', bbox_to_anchor=(1.02, 1), loc='upper left')
        else:
            if hue_col and hue_col in df.columns:
                melted = plot_data.melt(id_vars=[hue_col], value_vars=y_cols,
                                         var_name='指标', value_name='数值')
                sns.violinplot(data=melted, x='指标', y='数值', hue=hue_col,
                               ax=ax, inner=inner, bw_adjust=bw_adjust,
                               palette=palette, orient=orient)
                ax.set_xlabel('指标')
                ax.set_ylabel('数值')
                ax.legend(title=hue_col, bbox_to_anchor=(1.02, 1), loc='upper left')
            else:
                melted = plot_data.melt(value_vars=y_cols, var_name='指标', value_name='数值')
                sns.violinplot(data=melted, x='指标', y='数值',
                               ax=ax, inner=inner, bw_adjust=bw_adjust,
                               palette=palette, orient=orient)
                ax.set_xlabel('指标')
                ax.set_ylabel('数值')
    elif x_col and y_col:
        if hue_col and hue_col in df.columns:
            sns.violinplot(x=x_col, y=y_col, hue=hue_col, **plot_params)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.legend(title=hue_col, bbox_to_anchor=(1.02, 1), loc='upper left')
        else:
            sns.violinplot(x=x_col, y=y_col, **plot_params)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
    elif y_col:
        if hue_col and hue_col in df.columns:
            sns.violinplot(y=y_col, hue=hue_col, **plot_params)
            ax.set_ylabel(y_col)
            ax.legend(title=hue_col, bbox_to_anchor=(1.02, 1), loc='upper left')
        else:
            sns.violinplot(y=y_col, **plot_params)
            ax.set_ylabel(y_col)
    elif x_col:
        if hue_col and hue_col in df.columns:
            sns.violinplot(x=x_col, hue=hue_col, **plot_params)
            ax.set_xlabel(x_col)
            ax.legend(title=hue_col, bbox_to_anchor=(1.02, 1), loc='upper left')
        else:
            sns.violinplot(x=x_col, **plot_params)
            ax.set_xlabel(x_col)
    else:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) > 0:
            sns.violinplot(data=df[numeric_cols], **plot_params)
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
            categorical_columns = df.select_dtypes(exclude=['number']).columns.tolist()
            preview = df.head(10).to_dict(orient='records')

            palettes = [
                {'value': 'Set2', 'name': 'Set2 (默认)'},
                {'value': 'Set1', 'name': 'Set1 (鲜艳)'},
                {'value': 'Set3', 'name': 'Set3 (柔和)'},
                {'value': 'deep', 'name': 'Deep (深色)'},
                {'value': 'muted', 'name': 'Muted (柔和)'},
                {'value': 'bright', 'name': 'Bright (明亮)'},
                {'value': 'pastel', 'name': 'Pastel (粉蜡)'},
                {'value': 'dark', 'name': 'Dark (暗黑)'},
                {'value': 'colorblind', 'name': 'Colorblind (色盲友好)'},
                {'value': 'RdBu', 'name': 'RdBu (红蓝)'},
                {'value': 'RdYlBu', 'name': 'RdYlBu (红黄蓝)'},
                {'value': 'Spectral', 'name': 'Spectral (光谱)'},
                {'value': 'coolwarm', 'name': 'CoolWarm (冷暖)'},
                {'value': 'viridis', 'name': 'Viridis (绿黄)'},
                {'value': 'plasma', 'name': 'Plasma (紫黄)'},
                {'value': 'inferno', 'name': 'Inferno (黑红黄)'}
            ]

            inner_options = [
                {'value': 'box', 'name': '箱线图 (默认)'},
                {'value': 'quartile', 'name': '四分位数'},
                {'value': 'point', 'name': '散点'},
                {'value': 'stick', 'name': '线条'},
                {'value': 'none', 'name': '无'}
            ]

            orient_options = [
                {'value': 'v', 'name': '垂直 (默认)'},
                {'value': 'h', 'name': '水平'}
            ]

            return jsonify({
                'success': True,
                'filename': filename,
                'columns': columns,
                'numeric_columns': numeric_columns,
                'categorical_columns': categorical_columns,
                'preview': preview,
                'total_rows': len(df),
                'palettes': palettes,
                'inner_options': inner_options,
                'orient_options': orient_options
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
    hue_col = data.get('hue_col')
    y_cols = data.get('y_cols')
    title = data.get('title', '小提琴图')
    inner = data.get('inner', 'box')
    orient = data.get('orient', 'v')
    palette = data.get('palette', 'Set2')

    if not filename:
        return jsonify({'error': '缺少文件名参数'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在，请先上传文件'}), 400

    try:
        df = read_data(filepath, filename)

        if y_cols and not isinstance(y_cols, list):
            y_cols = None
        if y_cols and len(y_cols) == 0:
            y_cols = None

        bw_adjust = calculate_bw_adjust(df, x_col, y_col, hue_col, y_cols)
        img_base64 = generate_violin_plot(
            df,
            x_col=x_col,
            y_col=y_col,
            hue_col=hue_col,
            y_cols=y_cols,
            title=title,
            inner=inner,
            orient=orient,
            palette=palette
        )

        stats = {}
        active_y_cols = y_cols if y_cols else ([y_col] if y_col else [])

        for yc in active_y_cols:
            if yc and yc in df.columns:
                if x_col and x_col in df.columns:
                    if hue_col and hue_col in df.columns:
                        for (x_val, hue_val), group_data in df.groupby([x_col, hue_col])[yc]:
                            key = f'{x_val} - {hue_val}'
                            if y_cols:
                                key = f'{yc} | {key}'
                            stats[key] = {
                                'count': int(group_data.count()),
                                'mean': float(group_data.mean()),
                                'std': float(group_data.std()),
                                'min': float(group_data.min()),
                                'median': float(group_data.median()),
                                'max': float(group_data.max())
                            }
                    else:
                        for group_val, group_data in df.groupby(x_col)[yc]:
                            key = str(group_val)
                            if y_cols:
                                key = f'{yc} | {key}'
                            stats[key] = {
                                'count': int(group_data.count()),
                                'mean': float(group_data.mean()),
                                'std': float(group_data.std()),
                                'min': float(group_data.min()),
                                'median': float(group_data.median()),
                                'max': float(group_data.max())
                            }
                else:
                    if hue_col and hue_col in df.columns:
                        for hue_val, group_data in df.groupby(hue_col)[yc]:
                            key = str(hue_val)
                            if y_cols:
                                key = f'{yc} | {key}'
                            stats[key] = {
                                'count': int(group_data.count()),
                                'mean': float(group_data.mean()),
                                'std': float(group_data.std()),
                                'min': float(group_data.min()),
                                'median': float(group_data.median()),
                                'max': float(group_data.max())
                            }
                    else:
                        col_data = df[yc]
                        key = yc if y_cols else 'overall'
                        stats[key] = {
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
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'生成图表失败: {str(e)}'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

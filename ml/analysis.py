import numpy as np
import pandas as pd
import pymc as pm
import plotly.express as px
import plotly.graph_objects as go

# example !!
# ratings_data = {
#     "config1": [5, 4, 5, 3, 2],
#     "config2": [4, 4, 3, 4],
#     "config3": [5, 5, 5, 4, 5, 5],
#     "config4": [3, 3, 2, 4],
#     "config5": [4, 5, 4],
#     "config6": [3, 2, 3, 3, 2],
#     "config7": [5, 5, 4, 4, 5],
#     "config8": [4, 3, 4, 3],
#     "config9": [5, 4, 4, 4, 5],
#     "config10": [3, 3, 4, 2]
# }

def test_confs(ratings_data, hdi_prob=0.94):
    data = []
    configs = []
    for config, ratings in ratings_data.items():
        data.extend(ratings)
        configs.extend([config] * len(ratings))
    df = pd.DataFrame({'config': configs, 'rating': data})
    df['config_idx'] = pd.Categorical(df['config']).codes
    unique_configs = pd.Categorical(df['config']).categories
    n_configs = len(unique_configs)
    
    with pm.Model() as model:
        mu_group = pm.Normal('mu_group', mu=3, sigma=1)
        sigma_group = pm.HalfNormal('sigma_group', sigma=1)
        a = pm.Normal('a', mu=mu_group, sigma=sigma_group, shape=n_configs)
        sigma = pm.HalfNormal('sigma', sigma=1)
        rating_obs = pm.Normal('rating_obs', mu=a[df['config_idx'].values], sigma=sigma, observed=df['rating'].values)
        trace = pm.sample(2000, tune=1000, target_accept=0.9, return_inferencedata=True)

    a_samples = trace.posterior['a']
    posterior_means = a_samples.mean(dim=['chain', 'draw']).values
    lower_quantiles = a_samples.quantile((1 - hdi_prob) / 2, dim=['chain', 'draw']).values
    upper_quantiles = a_samples.quantile(1 - (1 - hdi_prob) / 2, dim=['chain', 'draw']).values

    results_df = pd.DataFrame({
        'Конфигурация': unique_configs,
        'Апостериорное среднее': posterior_means,
        f'Нижний квантиль ({int((1-hdi_prob)/2*100)}%)': lower_quantiles,
        f'Верхний квантиль ({int((1+(hdi_prob))/2*100)}%)': upper_quantiles,
    }).sort_values(by='Апостериорное среднее', ascending=False)

    best_idx = np.argmax(posterior_means)
    best_config_name = unique_configs[best_idx]

    # p(config_i == best)
    draws = a_samples.stack(samples=("chain", "draw")).values  # shape (n_configs, n_samples)
    best_counts = np.argmax(draws, axis=0)
    best_probs = np.bincount(best_counts, minlength=n_configs) / draws.shape[1]

    results_df['P(лучшая конфигурация)'] = best_probs[results_df.index]

    best_upper = upper_quantiles[best_idx]
    significantly_worse = [
        config for i, (config, low) in enumerate(zip(unique_configs, lower_quantiles))
        if i != best_idx and low > upper_quantiles[best_idx]
    ]

    model_description_str = (
        f'Байесовская иерархическая модель состоит из следующих компонентов:\n'
        f'- Глобальное среднее рейтингов (mu_group) ~ N(3, 1)\n'
        f'- Глобальная дисперсия между конфигурациями (sigma_group) ~ HalfNormal(1)\n'
        f'- Оценка каждой конфигурации a[i] ~ N(mu_group, sigma_group)\n'
        f'- Общая дисперсия наблюдений (sigma) ~ HalfNormal(1)\n'
        f'- Наблюдаемые рейтинги: rating ~ N(a[config_idx], sigma)\n\n'
        f'Используемый HDI интервал: {int(hdi_prob * 100)}%\n'
    )

    fig_bar = px.bar(
        results_df,
        x='Конфигурация',
        y='Апостериорное среднее',
        error_y=results_df[f'Верхний квантиль ({int((1+(hdi_prob))/2*100)}%)'] - results_df['Апостериорное среднее'],
        error_y_minus=results_df['Апостериорное среднее'] - results_df[f'Нижний квантиль ({int((1-hdi_prob)/2*100)}%)'],
        color='P(лучшая конфигурация)',
        title='Апостериорные средние рейтинги с доверительными интервалами и вероятностью быть лучшей'
    )
    fig_bar.update_layout(template='plotly_white')

    fig_forest = go.Figure()
    for i, row in results_df.iterrows():
        fig_forest.add_trace(go.Scatter(
            x=[row[f'Нижний квантиль ({int((1-hdi_prob)/2*100)}%)'], row[f'Верхний квантиль ({int((1+(hdi_prob))/2*100)}%)']],
            y=[row['Конфигурация'], row['Конфигурация']],
            mode='lines',
            line=dict(color='royalblue', width=4),
            showlegend=False
        ))
        fig_forest.add_trace(go.Scatter(
            x=[row['Апостериорное среднее']],
            y=[row['Конфигурация']],
            mode='markers',
            marker=dict(color='firebrick', size=10),
            showlegend=False
        ))
    fig_forest.update_layout(
        title='Доверительные интервалы для параметров a каждой конфигурации',
        xaxis_title='Оценка',
        yaxis_title='Конфигурация',
        template='plotly_white'
    )

    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=list(results_df.columns),
            fill_color='lightgrey', align='left'
        ),
        cells=dict(
            values=[results_df[col].round(4) if results_df[col].dtype.kind in "fc" else results_df[col] for col in results_df.columns],
            fill_color='white', align='left'
        )
    )])
    fig_table.update_layout(title='Апостериорная таблица по конфигурациям')

    context = {
        'model_description': model_description_str,
        'best_config': best_config_name,
        'significantly_worse': significantly_worse,
        'results_df': results_df,
        'bar_chart_html': fig_bar.to_html(full_html=False),
        'forest_chart_html': fig_forest.to_html(full_html=False),
        'table_html': fig_table.to_html(full_html=False),
    }

    return context
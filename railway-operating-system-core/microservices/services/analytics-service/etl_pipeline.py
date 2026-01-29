"""
Data aggregation and ETL pipeline for analytics
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class AnalyticsETLPipeline:
    """ETL pipeline for analytics data processing"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def aggregate_daily_metrics(self, tenant_id: UUID, date: datetime) -> Dict[str, Any]:
        """Aggregate daily metrics for a tenant"""
        try:
            schema_name = f"tenant_{tenant_id.hex}"
            aggregations = {}

            # Aggregate route searches
            daily_searches = await self._aggregate_route_searches(schema_name, date)
            aggregations['daily_searches'] = daily_searches

            # Aggregate API metrics
            daily_api_metrics = await self._aggregate_api_metrics(schema_name, date)
            aggregations['daily_api_metrics'] = daily_api_metrics

            # Aggregate cache metrics
            daily_cache_metrics = await self._aggregate_cache_metrics(schema_name, date)
            aggregations['daily_cache_metrics'] = daily_cache_metrics

            # Store aggregations
            await self._store_aggregations(tenant_id, aggregations, date)

            return aggregations

        except Exception as e:
            logger.error(f"Error aggregating daily metrics: {e}")
            raise

    async def _aggregate_route_searches(self, schema_name: str, date: datetime) -> Dict[str, Any]:
        """Aggregate route search metrics for a day"""
        try:
            query = f"""
                SELECT
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as searches,
                    AVG(route_score) as avg_score,
                    MIN(route_score) as min_score,
                    MAX(route_score) as max_score
                FROM {schema_name}.route_search_metrics
                WHERE DATE(created_at) = $1
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour
            """

            async with self.db_manager.get_session(schema_name) as session:
                results = await session.fetch(query, date.date())
                return {
                    'date': date.date().isoformat(),
                    'hourly_data': [dict(row) for row in results],
                    'total_searches': sum(r['searches'] for r in results),
                    'average_score': sum(r['avg_score'] * r['searches'] for r in results) / sum(r['searches'] for r in results) if results else 0
                }

        except Exception as e:
            logger.error(f"Error aggregating route searches: {e}")
            return {}

    async def _aggregate_api_metrics(self, schema_name: str, date: datetime) -> Dict[str, Any]:
        """Aggregate API performance metrics for a day"""
        try:
            query = f"""
                SELECT
                    endpoint,
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM {schema_name}.api_metrics
                WHERE DATE(created_at) = $1
                GROUP BY endpoint
            """

            async with self.db_manager.get_session(schema_name) as session:
                results = await session.fetch(query, date.date())
                return {
                    'date': date.date().isoformat(),
                    'endpoints': [dict(row) for row in results],
                    'total_requests': sum(r['total_requests'] for r in results),
                    'avg_response_time': sum(r['avg_response_time'] * r['total_requests'] for r in results) / sum(r['total_requests'] for r in results) if results else 0,
                    'error_rate': sum(r['errors'] for r in results) / sum(r['total_requests'] for r in results) if results else 0
                }

        except Exception as e:
            logger.error(f"Error aggregating API metrics: {e}")
            return {}

    async def _aggregate_cache_metrics(self, schema_name: str, date: datetime) -> Dict[str, Any]:
        """Aggregate cache performance metrics for a day"""
        try:
            query = f"""
                SELECT
                    cache_type,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    ROUND(
                        (SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::decimal / COUNT(*)) * 100,
                        2
                    ) as hit_rate
                FROM {schema_name}.cache_metrics
                WHERE DATE(created_at) = $1
                GROUP BY cache_type
            """

            async with self.db_manager.get_session(schema_name) as session:
                results = await session.fetch(query, date.date())
                return {
                    'date': date.date().isoformat(),
                    'cache_types': [dict(row) for row in results],
                    'overall_hit_rate': sum(r['cache_hits'] for r in results) / sum(r['total_requests'] for r in results) if results else 0
                }

        except Exception as e:
            logger.error(f"Error aggregating cache metrics: {e}")
            return {}

    async def _store_aggregations(self, tenant_id: UUID, aggregations: Dict[str, Any],
                                 date: datetime):
        """Store aggregated data in analytics tables"""
        try:
            schema_name = f"tenant_{tenant_id.hex}"

            # Build INSERT statements for aggregated metrics
            metric_inserts = []

            # Store daily search metrics
            if 'daily_searches' in aggregations:
                search_data = aggregations['daily_searches']
                metric_inserts.append({
                    'metric_name': 'daily_searches',
                    'metric_value': search_data.get('total_searches', 0),
                    'metric_type': 'count',
                    'period_start': date,
                    'period_end': date + timedelta(days=1)
                })

            # Store daily API metrics
            if 'daily_api_metrics' in aggregations:
                api_data = aggregations['daily_api_metrics']
                metric_inserts.append({
                    'metric_name': 'avg_response_time',
                    'metric_value': api_data.get('avg_response_time', 0),
                    'metric_type': 'duration',
                    'period_start': date,
                    'period_end': date + timedelta(days=1)
                })

            # Execute batch insert
            if metric_inserts:
                async with self.db_manager.get_session(schema_name) as session:
                    for metric in metric_inserts:
                        insert_query = f"""
                            INSERT INTO {schema_name}.analytics_metrics
                            (tenant_id, metric_name, metric_value, metric_type, 
                             period_start, period_end, computed_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """
                        await session.execute(
                            insert_query,
                            tenant_id, metric['metric_name'], metric['metric_value'],
                            metric['metric_type'], metric['period_start'],
                            metric['period_end'], datetime.utcnow()
                        )

        except Exception as e:
            logger.error(f"Error storing aggregations: {e}")
            raise

    async def backfill_analytics(self, tenant_id: UUID, start_date: datetime,
                                end_date: datetime):
        """Backfill analytics data for a date range"""
        try:
            current_date = start_date
            while current_date <= end_date:
                logger.info(f"Backfilling analytics for {current_date.date()}")
                await self.aggregate_daily_metrics(tenant_id, current_date)
                current_date += timedelta(days=1)

            logger.info(f"Backfill completed for {tenant_id}")

        except Exception as e:
            logger.error(f"Error in analytics backfill: {e}")
            raise

class DataQualityChecker:
    """Check data quality and consistency"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def validate_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """Validate metrics for a tenant"""
        try:
            validation_results = {
                'schema_name': f"tenant_{tenant_id.hex}",
                'checks': {}
            }

            schema_name = f"tenant_{tenant_id.hex}"

            # Check for missing or NULL values
            null_check = await self._check_null_values(schema_name)
            validation_results['checks']['null_values'] = null_check

            # Check for data consistency
            consistency_check = await self._check_data_consistency(schema_name)
            validation_results['checks']['consistency'] = consistency_check

            # Check for outliers
            outlier_check = await self._check_outliers(schema_name)
            validation_results['checks']['outliers'] = outlier_check

            return validation_results

        except Exception as e:
            logger.error(f"Error validating metrics: {e}")
            raise

    async def _check_null_values(self, schema_name: str) -> Dict[str, Any]:
        """Check for NULL values in key columns"""
        try:
            query = f"""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(response_time_ms) as non_null_response_times,
                    COUNT(*) - COUNT(response_time_ms) as null_response_times
                FROM {schema_name}.api_metrics
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """

            async with self.db_manager.get_session(schema_name) as session:
                result = await session.fetchrow(query)
                return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Error checking NULL values: {e}")
            return {}

    async def _check_data_consistency(self, schema_name: str) -> Dict[str, Any]:
        """Check data consistency"""
        try:
            # Verify that metric values are within reasonable ranges
            consistency_results = {}

            # Check response times (should be positive)
            query = f"""
                SELECT COUNT(*) as invalid_response_times
                FROM {schema_name}.api_metrics
                WHERE response_time_ms < 0 OR response_time_ms > 60000
            """

            async with self.db_manager.get_session(schema_name) as session:
                result = await session.fetchrow(query)
                consistency_results['invalid_response_times'] = result['invalid_response_times'] if result else 0

            return consistency_results

        except Exception as e:
            logger.error(f"Error checking data consistency: {e}")
            return {}

    async def _check_outliers(self, schema_name: str) -> Dict[str, Any]:
        """Detect statistical outliers"""
        try:
            query = f"""
                SELECT
                    AVG(response_time_ms) as avg_response_time,
                    STDDEV(response_time_ms) as stddev_response_time,
                    MAX(response_time_ms) as max_response_time
                FROM {schema_name}.api_metrics
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """

            async with self.db_manager.get_session(schema_name) as session:
                result = await session.fetchrow(query)
                return dict(result) if result else {}

        except Exception as e:
            logger.error(f"Error checking outliers: {e}")
            return {}